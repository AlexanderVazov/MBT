import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_bluetooth_serial/flutter_bluetooth_serial.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:flutter_spinkit/flutter_spinkit.dart';
import 'dart:io';

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
  bool _isConnected = false;
  String? _lastError;

  @override
  void initState() {
    super.initState();
    _initBluetooth();
  }

  Future<void> _initBluetooth() async {
    if (!Platform.isAndroid) return;
    try {
      final statuses = await [
        Permission.bluetoothScan,
        Permission.bluetoothConnect,
        Permission.locationWhenInUse,
      ].request();

      debugPrint('Bluetooth permission status: '
          'scan=${statuses[Permission.bluetoothScan]}, '
          'connect=${statuses[Permission.bluetoothConnect]}, '
          'location=${statuses[Permission.locationWhenInUse]}');

      final isEnabled = await FlutterBluetoothSerial.instance.isEnabled;
      if (isEnabled != true) {
        debugPrint('Bluetooth adapter is OFF. Requesting enable...');
        await FlutterBluetoothSerial.instance.requestEnable();
      }
    } catch (e) {
      debugPrint('Permission error: $e');
    }
  }

  Future<void> _scanForDevices() async {
    setState(() { _isScanning = true; _devicesList = []; _lastError = null; });
    try {
      final results = await FlutterBluetoothSerial.instance.getBondedDevices();
      setState(() { _devicesList = results; });
    } catch (e) {
      setState(() => _lastError = e.toString());
    } finally {
      setState(() => _isScanning = false);
    }
  }

  Future<BluetoothConnection> _connectWithRetry(String address) async {
    try {
      return await BluetoothConnection.toAddress(address)
          .timeout(const Duration(seconds: 15));
    } catch (firstError) {
      debugPrint('First connection attempt failed: $firstError');
      await Future.delayed(const Duration(milliseconds: 900));
      return BluetoothConnection.toAddress(address)
          .timeout(const Duration(seconds: 15));
    }
  }

  Future<void> _connectToDevice(BluetoothDevice device) async {
    if (_isConnecting) {
      debugPrint('Connection already in progress. Ignoring duplicate tap.');
      return;
    }

    final isEnabled = await FlutterBluetoothSerial.instance.isEnabled;
    if (isEnabled != true) {
      setState(() {
        _lastError = 'Bluetooth is disabled. Please enable it and try again.';
      });
      return;
    }

    if (device.isBonded != true) {
      setState(() {
        _lastError = 'Device is not paired. Pair it in Android Bluetooth settings first.';
      });
      return;
    }

    debugPrint('--- Attempting connection to ${device.name} (${device.address}) ---');
    setState(() {
      _lastError = null;
      _isConnecting = true;
    });

    try {
      await _connection?.finish();
      _connection = null;
    } catch (_) {
      // Ignore stale connection cleanup failures.
    }

    try {
      final connection = await _connectWithRetry(device.address);
      debugPrint('Connected to ${device.name}');

      if (!mounted) return;
      setState(() {
        _connection = connection;
        _isConnected = true;
      });

      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => WiFiSetupPage(connection: connection, device: device),
        ),
      );
    } catch (e) {
      debugPrint('CONNECTION ERROR: $e');
      if (!mounted) return;
      setState(() {
        _isConnected = false;
        _lastError = 'Failed to connect. Ensure Raspberry Pi RFCOMM service is running.';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isConnecting = false;
        });
      }
    }
  }

  @override
  void dispose() {
    try {
      _connection?.dispose();
    } catch (_) {
      // Ignore dispose errors while screen is closing.
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ElevatedButton.icon(
            onPressed: _isScanning ? null : _scanForDevices,
            icon: const Icon(Icons.bluetooth_searching),
            label: Text(_isScanning ? 'Scanning...' : 'Scan for Bonded Devices'),
          ),
          const SizedBox(height: 6),
          if (_isConnecting)
            const Text(
              'Connecting... please wait',
              style: TextStyle(fontSize: 12, color: Colors.blueGrey),
            ),
          const SizedBox(height: 10),
          if (_lastError != null)
            Container(
              padding: const EdgeInsets.all(8),
              color: Colors.red[50],
              child: Text('Error: $_lastError', style: const TextStyle(color: Colors.red, fontSize: 12)),
            ),
          const SizedBox(height: 10),
          const Text('RPi Setup Tip:', style: TextStyle(fontWeight: FontWeight.bold)),
          const Text('Ensure "sudo rfcomm watch hci0" is running on your Pi.', style: TextStyle(fontSize: 12)),
          const Divider(),
          Expanded(
            child: ListView.builder(
              itemCount: _devicesList.length,
              itemBuilder: (context, index) {
                final device = _devicesList[index];
                return ListTile(
                  title: Text(device.name ?? 'Unknown'),
                  subtitle: Text(device.address),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: _isConnecting ? null : () => _connectToDevice(device),
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
      body: const Center(child: Text('Connected! You can now send WiFi details.')),
    );
  }
}

class TextBoxPage extends StatelessWidget {
  const TextBoxPage({Key? key}) : super(key: key);
  @override
  Widget build(BuildContext context) => const Center(child: Text('Text Box Page'));
}

class EmptyPage extends StatelessWidget {
  const EmptyPage({Key? key}) : super(key: key);
  @override
  Widget build(BuildContext context) => const Center(child: Text('Empty Page'));
}
