import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_bluetooth_serial/flutter_bluetooth_serial.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:flutter_spinkit/flutter_spinkit.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:path_provider/path_provider.dart';
import 'dart:io';
import 'dart:async';
import 'dart:typed_data';
import 'dart:convert';

// Settings Manager - Central storage for all app settings
class SettingsManager {
  static final SettingsManager _instance = SettingsManager._internal();
  factory SettingsManager() => _instance;
  SettingsManager._internal();

  Map<String, dynamic> _settings = {
    'language': 'en',
    'ttsSpeed': 100.0,
    'favoriteFoods': '',
    'allergies': <String>[],
  };

  Future<File> _getSettingsFile() async {
    final directory = await getApplicationDocumentsDirectory();
    return File('${directory.path}/app_settings.json');
  }

  Future<void> loadSettings() async {
    try {
      final file = await _getSettingsFile();
      if (await file.exists()) {
        final contents = await file.readAsString();
        _settings = jsonDecode(contents);
        debugPrint('📖 Loaded settings: $_settings');
      } else {
        debugPrint('📄 No settings file found, using defaults');
      }
    } catch (e) {
      debugPrint('❌ Error loading settings: $e');
    }
  }

  Future<void> saveSettings() async {
    try {
      final file = await _getSettingsFile();
      await file.writeAsString(jsonEncode(_settings));
      debugPrint('✅ Saved settings: $_settings');
    } catch (e) {
      debugPrint('❌ Error saving settings: $e');
    }
  }

  String get language => _settings['language'] as String;
  set language(String value) {
    _settings['language'] = value;
    saveSettings();
  }

  double get ttsSpeed => _settings['ttsSpeed'] as double;
  set ttsSpeed(double value) {
    _settings['ttsSpeed'] = value;
    saveSettings();
  }

  String get favoriteFoods => _settings['favoriteFoods'] as String;
  set favoriteFoods(String value) {
    _settings['favoriteFoods'] = value;
    saveSettings();
  }

  List<String> get allergies => List<String>.from(_settings['allergies'] as List);
  set allergies(List<String> value) {
    _settings['allergies'] = value;
    saveSettings();
  }

  void toggleAllergy(String allergy, bool value) {
    final currentAllergies = allergies;
    if (value && !currentAllergies.contains(allergy)) {
      currentAllergies.add(allergy);
    } else if (!value) {
      currentAllergies.remove(allergy);
    }
    allergies = currentAllergies;
  }

  bool hasAllergy(String allergy) {
    return allergies.contains(allergy);
  }

  Map<String, dynamic> getAllSettings() => Map.from(_settings);
}

// Simple localization class
class AppLocalizations {
  final Locale locale;
  AppLocalizations(this.locale);

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate = _AppLocalizationsDelegate();

  static final Map<String, Map<String, String>> _localizedValues = {
    'en': {
      'appTitle': 'RPI Bridge',
      'connect': 'Connect',
      'foodPreferences': 'Food Preferences',
      'settings': 'Settings',
      'scanning': 'Scanning...',
      'refreshBondedDevices': 'Refresh Bonded Devices',
      'creatingRFCOMM': 'Creating RFCOMM Link...',
      'status': 'Status',
      'bondedDevices': 'Bonded Devices:',
      'unknown': 'Unknown',
      'setup': 'Setup',
      'wifiSSID': 'WiFi SSID',
      'enterSSID': 'Enter WiFi network name',
      'wifiPassword': 'WiFi Password',
      'enterPassword': 'Enter WiFi password',
      'configuring': 'Configuring...',
      'configureWiFi': 'Configure WiFi',
      'piResponse': 'Pi Response:',
      'favoriteFoods': 'Favorite Foods',
      'enterFavoriteFoods': 'Enter your favorite foods...',
      'allergiesIntolerances': 'Allergies & Intolerances',
      'selectAllergies': 'Select any allergies or intolerances you have:',
      'dairy': 'Dairy',
      'eggs': 'Eggs',
      'peanuts': 'Peanuts',
      'treeNuts': 'Tree Nuts',
      'soy': 'Soy',
      'wheatGluten': 'Wheat/Gluten',
      'fish': 'Fish',
      'shellfish': 'Shellfish',
      'sesame': 'Sesame',
      'lactose': 'Lactose',
      'language': 'Language',
      'english': 'English',
      'bulgarian': 'Bulgarian',
      'ttsSpeed': 'TTS Speed',
    },
    'bg': {
      'appTitle': 'RPI Мост',
      'connect': 'Свързване',
      'foodPreferences': 'Хранителни Предпочитания',
      'settings': 'Настройки',
      'scanning': 'Сканиране...',
      'refreshBondedDevices': 'Обнови Сдвоени Устройства',
      'creatingRFCOMM': 'Създаване на RFCOMM Връзка...',
      'status': 'Състояние',
      'bondedDevices': 'Сдвоени Устройства:',
      'unknown': 'Неизвестно',
      'setup': 'Настройка',
      'wifiSSID': 'WiFi SSID',
      'enterSSID': 'Въведете име на WiFi мрежа',
      'wifiPassword': 'WiFi Парола',
      'enterPassword': 'Въведете WiFi парола',
      'configuring': 'Конфигуриране...',
      'configureWiFi': 'Конфигурирай WiFi',
      'piResponse': 'Отговор от Pi:',
      'favoriteFoods': 'Любими Храни',
      'enterFavoriteFoods': 'Въведете вашите любими храни...',
      'allergiesIntolerances': 'Алергии и Непоносимости',
      'selectAllergies': 'Изберете алергии или непоносимости:',
      'dairy': 'Млечни Продукти',
      'eggs': 'Яйца',
      'peanuts': 'Фъстъци',
      'treeNuts': 'Ядки',
      'soy': 'Соя',
      'wheatGluten': 'Пшеница/Глутен',
      'fish': 'Риба',
      'shellfish': 'Миди',
      'sesame': 'Сусам',
      'lactose': 'Лактоза',
      'language': 'Език',
      'english': 'Английски',
      'bulgarian': 'Български',
      'ttsSpeed': 'Скорост на Глас',
    },
  };

  String translate(String key) {
    return _localizedValues[locale.languageCode]?[key] ?? key;
  }
}

class _AppLocalizationsDelegate extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  bool isSupported(Locale locale) => ['en', 'bg'].contains(locale.languageCode);

  @override
  Future<AppLocalizations> load(Locale locale) async {
    return AppLocalizations(locale);
  }

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await SettingsManager().loadSettings();
  
  FlutterError.onError = (FlutterErrorDetails details) {
    FlutterError.presentError(details);
    debugPrint('FLUTTER ERROR: ${details.exception}');
  };
  runApp(const MyApp());
}

class MyApp extends StatefulWidget {
  const MyApp({Key? key}) : super(key: key);
  
  static void setLocale(BuildContext context, Locale newLocale) {
    _MyAppState? state = context.findAncestorStateOfType<_MyAppState>();
    state?.setLocale(newLocale);
  }

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  late Locale _locale;

  @override
  void initState() {
    super.initState();
    _locale = Locale(SettingsManager().language);
  }

  void setLocale(Locale locale) {
    setState(() {
      _locale = locale;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'RPI Bridge',
      theme: ThemeData(primarySwatch: Colors.blue, useMaterial3: true),
      locale: _locale,
      supportedLocales: const [
        Locale('en', ''),
        Locale('bg', ''),
      ],
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
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
    final localizations = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(
        toolbarHeight: 0,
        elevation: 0,
      ),
      body: _pages[_selectedIndex],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: (i) => setState(() => _selectedIndex = i),
        items: [
          BottomNavigationBarItem(icon: const Icon(Icons.bluetooth), label: localizations.translate('connect')),
          BottomNavigationBarItem(icon: const Icon(Icons.local_dining), label: localizations.translate('foodPreferences')),
          BottomNavigationBarItem(icon: const Icon(Icons.settings), label: localizations.translate('settings')),
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
      await serial.cancelDiscovery();
      await Future.delayed(const Duration(milliseconds: 2500));

      if (_connection != null) {
        try { await _connection!.finish(); } catch (_) {}
        _connection = null;
      }

      BluetoothConnection connection;
      try {
        connection = await _connectSocket(device.address);
      } catch (firstError) {
        final msg = firstError.toString().toLowerCase();
        if (msg.contains('read failed') || msg.contains('timeout')) {
          final refreshed = await _refreshBond(device);
          if (!refreshed) rethrow;
          connection = await _connectSocket(device.address);
        } else {
          rethrow;
        }
      }

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
            _lastError = 'Cannot connect to ${device.name}. Ensure Pi server is running.';
          } else {
            _lastError = 'Connection failed: ${_compactError(e)}';
          }
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final localizations = AppLocalizations.of(context);
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ElevatedButton.icon(
            onPressed: _isScanning || _isConnecting ? null : _scanForDevices,
            icon: const Icon(Icons.bluetooth_searching),
            label: Text(_isScanning ? localizations.translate('scanning') : localizations.translate('refreshBondedDevices')),
          ),
          const SizedBox(height: 10),
          if (_isConnecting) 
             Row(children: [
              const SpinKitThreeBounce(color: Colors.blue, size: 20),
              const SizedBox(width: 10),
              Text(localizations.translate('creatingRFCOMM'), style: const TextStyle(color: Colors.blue, fontWeight: FontWeight.bold))
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
              child: Text('${localizations.translate('status')}: $_lastError', maxLines: 3, overflow: TextOverflow.ellipsis, style: const TextStyle(color: Colors.red, fontSize: 13)),
            ),
          const Divider(height: 30),
          Text(localizations.translate('bondedDevices'), style: const TextStyle(fontWeight: FontWeight.bold)),
          Expanded(
            child: ListView.builder(
              itemCount: _devicesList.length,
              itemBuilder: (context, index) {
                final device = _devicesList[index];
                return Card(
                  child: ListTile(
                    leading: const Icon(Icons.memory),
                    title: Text(device.name ?? localizations.translate('unknown')),
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

class WiFiSetupPage extends StatefulWidget {
  final BluetoothConnection connection;
  final BluetoothDevice device;
  const WiFiSetupPage({Key? key, required this.connection, required this.device}) : super(key: key);

  @override
  State<WiFiSetupPage> createState() => _WiFiSetupPageState();
}

class _WiFiSetupPageState extends State<WiFiSetupPage> {
  final TextEditingController _ssidController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  bool _isSending = false;
  String? _statusMessage;
  bool _passwordVisible = false;
  String _response = '';

  @override
  void initState() {
    super.initState();
    _listenForResponses();
  }

  void _listenForResponses() {
    widget.connection.input?.listen((data) {
      final message = String.fromCharCodes(data).trim();
      debugPrint('Received from Pi: $message');
      setState(() {
        _response += '$message\n';
        if (message.contains('SUCCESS')) {
          _statusMessage = '✓ WiFi configured successfully!';
          _isSending = false;
        } else if (message.contains('ERROR')) {
          _statusMessage = '✗ Configuration failed: $message';
          _isSending = false;
        }
      });
    }).onDone(() {
      debugPrint('Connection closed');
      if (mounted) {
        setState(() {
          _statusMessage = 'Connection closed';
          _isSending = false;
        });
      }
    });
  }

  Future<void> _sendWiFiCredentials() async {
    final ssid = _ssidController.text.trim();
    final password = _passwordController.text.trim();

    if (ssid.isEmpty) {
      setState(() => _statusMessage = 'Please enter WiFi name (SSID)');
      return;
    }

    setState(() {
      _isSending = true;
      _statusMessage = 'Sending WiFi credentials...';
      _response = '';
    });

    try {
      final payload = 'WIFI:$ssid:$password\n';
      widget.connection.output.add(Uint8List.fromList(payload.codeUnits));
      await widget.connection.output.allSent;
      
      debugPrint('Sent WiFi credentials: SSID=$ssid');
    } catch (e) {
      setState(() {
        _statusMessage = 'Error sending credentials: $e';
        _isSending = false;
      });
    }
  }

  @override
  void dispose() {
    _ssidController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final localizations = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text('${localizations.translate('setup')} ${widget.device.name}')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Icon(Icons.wifi, color: Colors.blue, size: 80),
            const SizedBox(height: 20),
            Text(
              localizations.translate('configureWiFi'),
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 10),
            Text(
              'Enter your WiFi credentials to configure ${widget.device.name}',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.grey[600]),
            ),
            const SizedBox(height: 40),
            TextField(
              controller: _ssidController,
              decoration: InputDecoration(
                labelText: localizations.translate('wifiSSID'),
                border: const OutlineInputBorder(),
                prefixIcon: const Icon(Icons.wifi),
                hintText: localizations.translate('enterSSID'),
              ),
              enabled: !_isSending,
            ),
            const SizedBox(height: 20),
            TextField(
              controller: _passwordController,
              obscureText: !_passwordVisible,
              decoration: InputDecoration(
                labelText: localizations.translate('wifiPassword'),
                border: const OutlineInputBorder(),
                prefixIcon: const Icon(Icons.lock),
                hintText: localizations.translate('enterPassword'),
                suffixIcon: IconButton(
                  icon: Icon(_passwordVisible ? Icons.visibility : Icons.visibility_off),
                  onPressed: () => setState(() => _passwordVisible = !_passwordVisible),
                ),
              ),
              enabled: !_isSending,
            ),
            const SizedBox(height: 30),
            ElevatedButton.icon(
              onPressed: _isSending ? null : _sendWiFiCredentials,
              icon: _isSending 
                ? const SizedBox(
                    width: 20, 
                    height: 20, 
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Icon(Icons.send),
              label: Text(_isSending ? localizations.translate('configuring') : localizations.translate('configureWiFi')),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
                textStyle: const TextStyle(fontSize: 16),
              ),
            ),
            const SizedBox(height: 20),
            if (_statusMessage != null)
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: _statusMessage!.contains('✓') ? Colors.green[50] : Colors.orange[50],
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: _statusMessage!.contains('✓') ? Colors.green : Colors.orange,
                  ),
                ),
                child: Text(
                  _statusMessage!,
                  style: TextStyle(
                    color: _statusMessage!.contains('✓') ? Colors.green[900] : Colors.orange[900],
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            if (_response.isNotEmpty)
              Container(
                margin: const EdgeInsets.only(top: 10),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.grey[100],
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('${localizations.translate('piResponse')}', style: const TextStyle(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    Text(_response, style: const TextStyle(fontFamily: 'monospace', fontSize: 12)),
                  ],
                ),
              ),
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
  final SettingsManager _settings = SettingsManager();
  Timer? _debounceTimer;
  
  // Track allergy/intolerance selections using localization keys
  final Map<String, bool> _allergies = {
    'dairy': false,
    'eggs': false,
    'peanuts': false,
    'treeNuts': false,
    'soy': false,
    'wheatGluten': false,
    'fish': false,
    'shellfish': false,
    'sesame': false,
    'lactose': false,
  };

  @override
  void initState() {
    super.initState();
    _loadPreferences();
  }

  void _loadPreferences() {
    // Load favorite foods
    _favoriteFoodsController.text = _settings.favoriteFoods;
    
    // Load allergies
    for (var key in _allergies.keys) {
      _allergies[key] = _settings.hasAllergy(key);
    }
    
    setState(() {});
    debugPrint('📖 Loaded food preferences');
  }

  void _saveFavoriteFoods(String value) {
    // Cancel any existing timer
    _debounceTimer?.cancel();
    
    // Start a new timer - only save after 500ms of no typing
    _debounceTimer = Timer(const Duration(milliseconds: 500), () {
      _settings.favoriteFoods = value;
      debugPrint('✅ Saved favorite foods');
    });
  }

  void _saveAllergy(String key, bool value) {
    _settings.toggleAllergy(key, value);
  }

  @override
  void dispose() {
    _debounceTimer?.cancel();
    _favoriteFoodsController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final localizations = AppLocalizations.of(context);
    
    return SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              localizations.translate('favoriteFoods'),
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _favoriteFoodsController,
              decoration: InputDecoration(
                border: const OutlineInputBorder(),
                hintText: localizations.translate('enterFavoriteFoods'),
              ),
              maxLines: 3,
              onChanged: (value) => _saveFavoriteFoods(value),
            ),
            const SizedBox(height: 24),
            Text(
              localizations.translate('allergiesIntolerances'),
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              localizations.translate('selectAllergies'),
              style: const TextStyle(fontSize: 14, color: Colors.grey),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8.0,
              runSpacing: 8.0,
              children: _allergies.keys.map((allergyKey) {
                return FilterChip(
                  label: Text(localizations.translate(allergyKey)),
                  selected: _allergies[allergyKey]!,
                  onSelected: (bool selected) {
                    setState(() {
                      _allergies[allergyKey] = selected;
                    });
                    _saveAllergy(allergyKey, selected);
                  },
                  selectedColor: Colors.orange.shade300,
                  checkmarkColor: Colors.white,
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }
}

class EmptyPage extends StatefulWidget {
  const EmptyPage({Key? key}) : super(key: key);
  @override
  State<EmptyPage> createState() => _EmptyPageState();
}

class _EmptyPageState extends State<EmptyPage> {
  final SettingsManager _settings = SettingsManager();
  late String _selectedLanguage;
  late double _ttsSpeed;
  Timer? _debounceTimer;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  void _loadSettings() {
    _selectedLanguage = _settings.language;
    _ttsSpeed = _settings.ttsSpeed;
    setState(() {});
    debugPrint('📖 Loaded settings page');
  }

  void _saveLanguage(String language) {
    _settings.language = language;
  }

  void _saveTTSSpeed(double speed) {
    // Cancel any existing timer
    _debounceTimer?.cancel();
    
    // Start a new timer - only save after 300ms of no changes
    _debounceTimer = Timer(const Duration(milliseconds: 300), () {
      _settings.ttsSpeed = speed;
      debugPrint('✅ Saved TTS speed: $speed');
    });
  }

  @override
  void dispose() {
    _debounceTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final localizations = AppLocalizations.of(context);
    
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            localizations.translate('language'),
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          DropdownButton<String>(
            value: _selectedLanguage,
            isExpanded: true,
            items: [
              DropdownMenuItem(value: 'en', child: Text(localizations.translate('english'))),
              DropdownMenuItem(value: 'bg', child: Text(localizations.translate('bulgarian'))),
            ],
            onChanged: (String? newValue) {
              if (newValue != null) {
                setState(() {
                  _selectedLanguage = newValue;
                });
                _saveLanguage(newValue);
                // Change the app locale
                MyApp.setLocale(context, Locale(newValue));
              }
            },
          ),
          const SizedBox(height: 32),
          Text(
            localizations.translate('ttsSpeed'),
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: Slider(
                  value: _ttsSpeed,
                  min: 1.0,
                  max: 200.0,
                  divisions: 99,
                  label: '${_ttsSpeed.round()}%',
                  onChanged: (double value) {
                    setState(() {
                      _ttsSpeed = value;
                    });
                    _saveTTSSpeed(value);
                  },
                ),
              ),
              SizedBox(
                width: 60,
                child: Text(
                  '${_ttsSpeed.round()}%',
                  style: const TextStyle(fontSize: 16),
                  textAlign: TextAlign.center,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
