import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_bluetooth_serial/flutter_bluetooth_serial.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:flutter_spinkit/flutter_spinkit.dart';
import 'dart:io';
import 'dart:async';

void main() {
  FlutterError.onError = (FlutterErrorDetails details) {
    FlutterError.presentError(details);
    debugPrint('FLUTTER ERROR: ${details.exception}');
  };
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'RPI Bridge',
      theme: ThemeData(primarySwatch: Colors.blue, useMaterial3: true),
      home: const MainScreen(),
    );
  }
}

class MainScreen extends StatefulWidget {
  const MainScreen({Key? key}) : super(key: key);
  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _selectedIndex = 0;
  final List<Widget> _pages = [
    const BluetoothConnectionPage(),
    const TextBoxPage(),
    const EmptyPage(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('RPI Bridge')),
      body: _pages[_selectedIndex],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: (i) => setState(() => _selectedIndex = i),
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.bluetooth), label: 'Connect'),
          BottomNavigationBarItem(icon: Icon(Icons.edit), label: 'Text Box'),
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Empty'),
        ],
      ),
    );
  }
}

class BluetoothConnectionPage extends StatefulWidget {
  const BluetoothConnectionPage({Key? key}) : super(key: key);
  @override
  State<BluetoothConnectionPage> createState() => _BluetoothConnectionPageState();
}

class _BluetoothConnectionPageState extends State<BluetoothConnectionPage> {
  List<BluetoothDevice> _devicesList = [];
  bool _isScanning = false;
  bool _isConnecting = false;
  BluetoothConnection? _connection;
  String? _lastError;

  String _compactError(Object error) {
    final raw = error.toString();
    final firstLine = raw.split('\n').first;
    if (firstLine.length <= 140) return firstLine;
    return '${firstLine.substring(0, 140)}...';
  }

  Future<bool> _refreshBond(BluetoothDevice device) async {
    final serial = FlutterBluetoothSerial.instance;
    try {
      debugPrint('Attempting bond refresh for ${device.address}');
      await serial.removeDeviceBondWithAddress(device.address);
      await Future.delayed(const Duration(milliseconds: 1500));
      final bonded = await serial.bondDeviceAtAddress(device.address);
      debugPrint('Bond refresh result for ${device.address}: $bonded');
      
      // Wait for the bonding process to fully complete before returning
      if (bonded == true) {
        debugPrint('Waiting for bond to stabilize...');
        await Future.delayed(const Duration(milliseconds: 2000));
      }
      
      return bonded == true;
    } catch (e) {
      debugPrint('Bond refresh failed: $e');
      return false;
    }
  }

  Future<BluetoothConnection> _connectSocket(String address) {
    return BluetoothConnection.toAddress(address)
        .timeout(const Duration(seconds: 20));
  }

  @override
  void initState() {
    super.initState();
    _initBluetooth();
  }

  Future<void> _initBluetooth() async {
    if (!Platform.isAndroid) return;
    try {
      // Requesting multiple permissions to ensure the stack is fully authorized
      await [
        Permission.bluetoothScan,
        Permission.bluetoothConnect,
        Permission.location,
        Permission.bluetooth,
      ].request();
    } catch (e) {
      debugPrint('Permission error: $e');
    }
  }

  Future<void> _scanForDevices() async {
    setState(() { _isScanning = true; _devicesList = []; _lastError = null; });
    try {
      // Ensure we aren't already discovering
      await FlutterBluetoothSerial.instance.cancelDiscovery();
      final results = await FlutterBluetoothSerial.instance.getBondedDevices();
      setState(() { _devicesList = results; });
    } catch (e) {
      setState(() => _lastError = e.toString());
    } finally {
      setState(() => _isScanning = false);
    }
  }

  Future<void> _connectToDevice(BluetoothDevice device) async {
    if (_isConnecting) return;

    setState(() {
      _isConnecting = true;
      _lastError = null;
    });

    debugPrint('--- Attempting Connection to ${device.name} (${device.address}) ---');

    try {
      final serial = FlutterBluetoothSerial.instance;
      final bondState = await serial.getBondStateForAddress(device.address);
      debugPrint('Bond state before connect: $bondState');

      // 1. CRITICAL: Cancel any background discovery
      await serial.cancelDiscovery();
      
      // 2. Wait for the adapter to settle after pairing
      debugPrint('Waiting for Bluetooth adapter to stabilize...');
      await Future.delayed(const Duration(milliseconds: 2500));

      // 3. Clean up any stale connection objects
      if (_connection != null) {
        try { await _connection!.finish(); } catch (_) {}
        _connection = null;
      }

      // 4. Try to connect with retry logic
      BluetoothConnection connection;
      try {
        debugPrint('Attempting first connection to ${device.address}...');
        connection = await _connectSocket(device.address);
        debugPrint('First connection attempt succeeded!');
      } catch (firstError) {
        debugPrint('First connect attempt failed: $firstError');
        final msg = firstError.toString().toLowerCase();
        
        // If read failed or timeout, it likely means the Pi server isn't running
        if (msg.contains('read failed') || msg.contains('timeout')) {
          debugPrint('Detected connection failure (Pi server may not be running)');
          debugPrint('Attempting bond refresh as fallback...');
          
          final refreshed = await _refreshBond(device);
          if (!refreshed) {
            throw Exception(
              'Connection failed. Make sure the Bluetooth server is running on the Raspberry Pi. '
              'Error: ${_compactError(firstError)}'
            );
          }

          debugPrint('Retrying connection after bond refresh...');
          
          try {
            connection = await _connectSocket(device.address);
            debugPrint('Second connection attempt succeeded!');
          } catch (secondError) {
            throw Exception(
              'Connection failed after bond refresh. '
              'Ensure the Raspberry Pi Bluetooth server (bt_server.py) is running. '
              'Error: ${_compactError(secondError)}'
            );
          }
        } else {
          rethrow;
        }
      }

      debugPrint('Connection Success!');

      if (mounted) {
        setState(() {
          _connection = connection;
          _isConnecting = false;
        });
        
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => WiFiSetupPage(connection: connection, device: device),
          ),
        );
      }
    } catch (e) {
      debugPrint('CONNECTION ATTEMPT FAILED: $e');
      if (mounted) {
        setState(() {
          _isConnecting = false;
          final errorMsg = e.toString();
          if (errorMsg.contains('read failed') || errorMsg.contains('timeout')) {
            _lastError = 'Cannot connect to ${device.name}. '
                'The Raspberry Pi Bluetooth server is not running. '
                'Run "sudo python3 bt_server.py" on the Pi first, then retry.';
          } else {
            _lastError = 'Connection failed: ${_compactError(e)}';
          }
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ElevatedButton.icon(
            onPressed: _isScanning || _isConnecting ? null : _scanForDevices,
            icon: const Icon(Icons.bluetooth_searching),
            label: Text(_isScanning ? 'Scanning...' : 'Refresh Bonded Devices'),
          ),
          const SizedBox(height: 10),
          if (_isConnecting) 
             const Row(children: [
               SpinKitThreeBounce(color: Colors.blue, size: 20),
               SizedBox(width: 10),
               Text('Creating RFCOMM Link...', style: TextStyle(color: Colors.blue, fontWeight: FontWeight.bold))
             ]),
          if (_lastError != null)
            Container(
              margin: const EdgeInsets.only(top: 10),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.red[50],
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.red.shade200)
              ),
              child: Text(
                'Status: $_lastError',
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(color: Colors.red, fontSize: 13),
              ),
            ),
          const Divider(height: 30),
          const Text('Bonded Devices:', style: TextStyle(fontWeight: FontWeight.bold)),
          Expanded(
            child: ListView.builder(
              itemCount: _devicesList.length,
              itemBuilder: (context, index) {
                final device = _devicesList[index];
                return Card(
                  child: ListTile(
                    leading: const Icon(Icons.memory),
                    title: Text(device.name ?? 'Unknown'),
                    subtitle: Text(device.address),
                    trailing: _isConnecting ? null : const Icon(Icons.login),
                    onTap: _isConnecting ? null : () => _connectToDevice(device),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class WiFiSetupPage extends StatelessWidget {
  final BluetoothConnection connection;
  final BluetoothDevice device;
  const WiFiSetupPage({Key? key, required this.connection, required this.device}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Setup ${device.name}')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.check_circle, color: Colors.green, size: 80),
            const SizedBox(height: 20),
            const Text('Bluetooth Connected!', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            Text('RFCOMM Link Established with ${device.name}'),
          ],
        ),
      ),
    );
  }
}

class TextBoxPage extends StatefulWidget {
  const TextBoxPage({Key? key}) : super(key: key);
  @override
  State<TextBoxPage> createState() => _TextBoxPageState();
}

class _TextBoxPageState extends State<TextBoxPage> {
  final TextEditingController _favoriteFoodsController = TextEditingController();
  final TextEditingController _allergiesController = TextEditingController();

  @override
  void dispose() {
    _favoriteFoodsController.dispose();
    _allergiesController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Favorite Foods',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _favoriteFoodsController,
            decoration: const InputDecoration(
              border: OutlineInputBorder(),
              hintText: 'Enter your favorite foods...',
            ),
            maxLines: 3,
          ),
          const SizedBox(height: 24),
          const Text(
            'Allergies',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _allergiesController,
            decoration: const InputDecoration(
              border: OutlineInputBorder(),
              hintText: 'Enter any allergies...',
            ),
            maxLines: 3,
          ),
        ],
      ),
    );
  }
}

class EmptyPage extends StatelessWidget {
  const EmptyPage({Key? key}) : super(key: key);
  @override
  Widget build(BuildContext context) => const Center(child: Text('Empty Page'));
}
