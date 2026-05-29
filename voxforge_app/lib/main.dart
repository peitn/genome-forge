import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

void main() {
  runApp(const VoxForgeApp());
}

// ─────────────────────────────────────────────────────────────────────────────
// THEME
// ─────────────────────────────────────────────────────────────────────────────

const _bg       = Color(0xFF090B13);
const _card     = Color(0xFF151827);
const _accent   = Color(0xFF7C5CFF);
const _accent2  = Color(0xFF00E5FF);
const _red      = Color(0xFFFF4B6E);
const _green    = Color(0xFF00E096);
const _orange   = Color(0xFFFF9800);
const _yellow   = Color(0xFFFFEB3B);

class VoxForgeApp extends StatelessWidget {
  const VoxForgeApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'VoxForge Ultimate Studio',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: _accent,
        brightness: Brightness.dark,
        scaffoldBackgroundColor: _bg,
        cardTheme: CardThemeData(
          color: _card,
          elevation: 0,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        ),
      ),
      home: const VoxForgeShell(),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// DATA MODELS
// ─────────────────────────────────────────────────────────────────────────────

class LogEntry {
  const LogEntry(this.title, this.detail, [this.level = 'info']);
  final String title, detail, level;
}

class CarPart {
  const CarPart(this.name, this.mass, this.slot);
  final String name, slot;
  final double mass;
}

class MpcCharacter {
  const MpcCharacter(this.name, this.role, this.category, this.level);
  final String name, role, category;
  final int level;
}

class RobotComponent {
  const RobotComponent(this.name, this.type, this.power);
  final String name, type;
  final double power;
}

class Vehicle {
  Vehicle(this.id, this.x, this.z, this.speed, this.type);
  final String id, type;
  double x, z, speed;
}

class RaceState {
  int lap = 0;
  double speed = 0;
  double fuel = 100;
  double tire = 1.0;
  double position = 0;
  bool finished = false;
  bool boost = false;
  double grip = 1.0;
  int tick = 0;
  List<String> events = [];
}

// ─────────────────────────────────────────────────────────────────────────────
// SHELL
// ─────────────────────────────────────────────────────────────────────────────

class VoxForgeShell extends StatefulWidget {
  const VoxForgeShell({super.key});
  @override
  State<VoxForgeShell> createState() => _VoxForgeShellState();
}

class _VoxForgeShellState extends State<VoxForgeShell>
    with TickerProviderStateMixin {

  int _idx = 0;
  late final AnimationController _pulse;

  final _rng = math.Random(1337);
  int _tick = 0;

  // Dashboard / fluid
  double _water = 32.4, _heat = 0.28, _fracture = 0.07, _aiSignal = 0.42;

  // City
  double _cityHealth = 0.87;
  String _weather = 'Clear';
  double _congestion = 0.23;
  int _activeRoadworks = 2;
  List<Vehicle> _vehicles = [];
  bool _simRunning = false;

  // Car builder
  final List<CarPart> _carParts = const [
    CarPart('V8 Engine',      220,  'engine'),
    CarPart('Carbon Chassis', 180,  'chassis'),
    CarPart('Front Axle',      48,  'axle_f'),
    CarPart('Rear Axle',       52,  'axle_r'),
    CarPart('Sport Wheel ×4',  64,  'wheels'),
    CarPart('Aero Kit',        18,  'aero'),
    CarPart('Brake System',    22,  'brakes'),
  ];
  String _suspension = 'Double Wishbone';
  double _dragCoeff = 0.31;
  double _downforce = 0.52;
  double _zero100  = 3.8;
  double _braking  = 28.4;

  // Character studio
  final List<MpcCharacter> _characters = const [
    MpcCharacter('Zara Knight',    'Guard',      'classic_city',  12),
    MpcCharacter('Ren Mori',       'Merchant',   'tech_city',     8),
    MpcCharacter('Cal Oris',       'Engineer',   'industrial',    15),
    MpcCharacter('Lysa Vance',     'Medic',      'classic_city',  10),
    MpcCharacter('Drax',           'Enforcer',   'wasteland',     18),
    MpcCharacter('Nova',           'Hacker',     'tech_city',     14),
    MpcCharacter('Piett',          'Navigator',  'coastal',       9),
    MpcCharacter('Kira Sol',       'Pilot',      'sky_city',      16),
    MpcCharacter('Brick',          'Worker',     'industrial',    7),
    MpcCharacter('Sable',          'Spy',        'metro',         20),
    MpcCharacter('Olo',            'Farmer',     'rural',         5),
    MpcCharacter('Vex',            'Scavenger',  'wasteland',     11),
  ];
  String _charFilter = 'All';

  // Robot factory
  final List<RobotComponent> _robotParts = [
    RobotComponent('Neural Core',      'CPU',       4.8),
    RobotComponent('Servo Arm ×2',     'Actuator',  2.2),
    RobotComponent('LiDAR Sensor',     'Sensor',    1.6),
    RobotComponent('Torso Frame',      'Structure', 0.0),
    RobotComponent('Power Cell 4000',  'Power',     3.1),
  ];
  bool _robotAssembled = false;
  double _robotEfficiency = 0.0;

  // 3-D studio
  String _tool = 'Voxel Brush';
  String _material = 'Photonic Alloy';
  double _brushSize = 2;
  bool _physicsRunning = false;
  final List<LogEntry> _logs = [
    const LogEntry('World init',    'Seed=1337, chunk grid ready'),
    const LogEntry('Studio ready',  '8 tools, 8 materials loaded'),
    const LogEntry('Engine v0.11.1','VoxForge Ultimate Studio online'),
  ];

  // Race
  final _race = RaceState();
  late final AnimationController _raceCtrl;

  @override
  void initState() {
    super.initState();
    _pulse = AnimationController(vsync: this, duration: const Duration(milliseconds: 1800))
      ..repeat(reverse: true);
    _raceCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 80))
      ..addListener(_raceTick);
    _spawnCityVehicles();
  }

  @override
  void dispose() {
    _pulse.dispose();
    _raceCtrl.dispose();
    super.dispose();
  }

  void _spawnCityVehicles() {
    _vehicles = List.generate(12, (i) => Vehicle(
      'V$i', _rng.nextDouble()*30, _rng.nextDouble()*30,
      0.3 + _rng.nextDouble()*0.7,
      i % 3 == 0 ? 'truck' : (i % 2 == 0 ? 'bus' : 'car'),
    ));
  }

  void _cityTick() {
    if (!_simRunning) return;
    setState(() {
      _tick++;
      for (final v in _vehicles) {
        v.x = (v.x + v.speed * 0.4 + _rng.nextDouble()*0.1) % 32;
        v.z = (v.z + v.speed * 0.2) % 32;
      }
      _congestion = 0.1 + 0.3 * math.sin(_tick * 0.05).abs() + _rng.nextDouble() * 0.05;
      _cityHealth  = (0.75 + 0.15 * math.cos(_tick * 0.03)).clamp(0, 1);
      _water    = (32.4 + 3 * math.sin(_tick * 0.07)).abs();
      _heat     = (0.2  + 0.15 * math.cos(_tick * 0.04)).clamp(0, 1);
      _fracture = (0.05 + 0.08 * math.sin(_tick * 0.09)).abs().clamp(0, 1);
      _aiSignal = (0.4  + 0.3  * math.sin(_tick * 0.06)).clamp(0, 1);
      if (_tick % 8 == 0) {
        _weather = const ['Clear','Cloudy','Rain','Storm','Fog','Snow'][_rng.nextInt(6)];
        _activeRoadworks = _rng.nextInt(5);
      }
      if (_tick % 5 == 0) {
        _addLog('Sim tick $_tick',
            'Health=${(_cityHealth*100).toStringAsFixed(1)}% '
            'Congestion=${(_congestion*100).toStringAsFixed(0)}%');
      }
    });
  }

  void _raceTick() {
    if (_race.finished) return;
    setState(() {
      _race.tick++;
      _race.speed = (_race.boost ? 240 : 180) * _race.grip + _rng.nextDouble() * 8;
      _race.position += _race.speed * 0.001;
      _race.fuel  = (_race.fuel  - 0.04 - (_race.boost ? 0.1 : 0)).clamp(0, 100);
      _race.tire  = (_race.tire  - 0.002).clamp(0, 1);
      _race.grip  = 0.6 + _race.tire * 0.4;
      if (_race.position >= 1.0 * (_race.lap + 1)) {
        _race.lap++;
        _race.events.insert(0, 'Lap ${_race.lap} — ${(_race.speed).toStringAsFixed(0)} km/h');
        if (_race.lap >= 3) { _race.finished = true; _raceCtrl.stop(); }
      }
      if (_race.fuel <= 0) { _race.finished = true; _raceCtrl.stop(); }
    });
  }

  void _assembleRobot() {
    setState(() {
      _robotAssembled = true;
      _robotEfficiency = _robotParts.fold(0.0, (s, p) => s + p.power)
          / (_robotParts.length * 5.0) * 100;
    });
    _addLog('Robot assembled', 'Efficiency ${_robotEfficiency.toStringAsFixed(1)}%', 'success');
  }

  void _addLog(String t, String d, [String level = 'info']) {
    _logs.insert(0, LogEntry(t, d, level));
    if (_logs.length > 20) _logs.removeLast();
  }

  static const _navItems = [
    NavigationDestination(icon: Icon(Icons.dashboard_outlined),      selectedIcon: Icon(Icons.dashboard),              label: 'Dashboard'),
    NavigationDestination(icon: Icon(Icons.location_city_outlined),  selectedIcon: Icon(Icons.location_city),          label: 'City'),
    NavigationDestination(icon: Icon(Icons.directions_car_outlined), selectedIcon: Icon(Icons.directions_car),         label: 'Cars'),
    NavigationDestination(icon: Icon(Icons.groups_outlined),         selectedIcon: Icon(Icons.groups),                 label: 'Characters'),
    NavigationDestination(icon: Icon(Icons.precision_manufacturing_outlined), selectedIcon: Icon(Icons.precision_manufacturing), label: 'Robots'),
    NavigationDestination(icon: Icon(Icons.view_in_ar_outlined),     selectedIcon: Icon(Icons.view_in_ar),             label: '3D Studio'),
    NavigationDestination(icon: Icon(Icons.sports_esports_outlined), selectedIcon: Icon(Icons.sports_esports),         label: 'Games'),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bg,
      body: IndexedStack(index: _idx, children: [
        _DashboardScreen(pulse: _pulse, water: _water, heat: _heat,
            fracture: _fracture, aiSignal: _aiSignal, cityHealth: _cityHealth, logs: _logs),
        _CityScreen(
          vehicles: _vehicles, cityHealth: _cityHealth, weather: _weather,
          congestion: _congestion, roadworks: _activeRoadworks,
          running: _simRunning, tick: _tick,
          onToggle: () {
            setState(() => _simRunning = !_simRunning);
            if (_simRunning) _citySimLoop();
          },
        ),
        _CarScreen(
          parts: _carParts, suspension: _suspension, drag: _dragCoeff,
          downforce: _downforce, zero100: _zero100, braking: _braking,
          onTune: () => setState(() {
            _dragCoeff  = 0.25 + _rng.nextDouble() * 0.15;
            _downforce  = 0.4  + _rng.nextDouble() * 0.3;
            _zero100    = 3.2  + _rng.nextDouble() * 1.2;
            _braking    = 22   + _rng.nextDouble() * 10;
            _suspension = const ['Double Wishbone','MacPherson','Multilink','Active'][_rng.nextInt(4)];
            _addLog('Car tuned', 'Drag=${_dragCoeff.toStringAsFixed(2)} '
                'Downforce=${_downforce.toStringAsFixed(2)}');
          }),
        ),
        _CharacterScreen(chars: _characters, filter: _charFilter,
            onFilter: (f) => setState(() => _charFilter = f)),
        _RobotScreen(
          parts: _robotParts, assembled: _robotAssembled,
          efficiency: _robotEfficiency, onAssemble: _assembleRobot,
          onReset: () => setState(() { _robotAssembled = false; _robotEfficiency = 0; }),
        ),
        _StudioScreen(
          pulse: _pulse, tool: _tool, material: _material,
          brushSize: _brushSize, physicsRunning: _physicsRunning, logs: _logs,
          tools: const ['Voxel Brush','Eraser','Material Paint','Fluid Source',
                        'Heat Injector','Fracture Probe','Agent Spawner','Prefab Stamp'],
          materials: const ['Photonic Alloy','Stone','Glass','Water',
                            'Lava','Carbon Fiber','Neon Circuit','Reactive Foam'],
          onTool:     (t) => setState(() { _tool = t; _addLog('Tool', t); }),
          onMaterial: (m) => setState(() => _material = m),
          onBrush:    (v) => setState(() => _brushSize = v),
          onPhysics:  () => setState(() {
            _physicsRunning = !_physicsRunning;
            _addLog('Physics', _physicsRunning ? 'started' : 'stopped');
          }),
        ),
        _GamesScreen(
          race: _race,
          onStartRace: () { if (!_race.finished) _raceCtrl.repeat(); },
          onBoost: (v) => setState(() => _race.boost = v),
          onResetRace: () => setState(() {
            _race
              ..lap=0 ..speed=0 ..fuel=100 ..tire=1
              ..position=0 ..finished=false ..boost=false
              ..grip=1 ..tick=0 ..events.clear();
            _raceCtrl.stop();
          }),
        ),
      ]),
      bottomNavigationBar: NavigationBar(
        backgroundColor: _card,
        selectedIndex: _idx,
        indicatorColor: _accent.withValues(alpha: 0.3),
        onDestinationSelected: (i) => setState(() => _idx = i),
        destinations: _navItems,
        labelBehavior: NavigationDestinationLabelBehavior.onlyShowSelected,
      ),
    );
  }

  void _citySimLoop() async {
    while (_simRunning && mounted) {
      _cityTick();
      await Future.delayed(const Duration(milliseconds: 400));
    }
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 1. DASHBOARD
// ─────────────────────────────────────────────────────────────────────────────

class _DashboardScreen extends StatelessWidget {
  const _DashboardScreen({required this.pulse, required this.water, required this.heat,
    required this.fracture, required this.aiSignal, required this.cityHealth, required this.logs});
  final AnimationController pulse;
  final double water, heat, fracture, aiSignal, cityHealth;
  final List<LogEntry> logs;

  @override
  Widget build(BuildContext context) {
    return CustomScrollView(slivers: [
      const SliverAppBar(pinned: true, backgroundColor: _bg,
        title: Text('VoxForge Ultimate Studio',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold))),
      SliverPadding(
        padding: const EdgeInsets.all(16),
        sliver: SliverGrid(
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2, mainAxisSpacing: 12, crossAxisSpacing: 12, childAspectRatio: 1.35),
          delegate: SliverChildListDelegate([
            _MetricCard('Water',       '${water.toStringAsFixed(1)} m³',         Icons.water,                 _accent2, water / 50),
            _MetricCard('Heat',        '${(heat*100).toStringAsFixed(0)}%',       Icons.local_fire_department, _orange,  heat),
            _MetricCard('Fracture',    '${(fracture*100).toStringAsFixed(0)}%',   Icons.broken_image,          _red,     fracture),
            _MetricCard('AI Signal',   '${(aiSignal*100).toStringAsFixed(0)}%',   Icons.hub,                   _green,   aiSignal),
            _MetricCard('City Health', '${(cityHealth*100).toStringAsFixed(0)}%', Icons.location_city,         _accent,  cityHealth),
            _MetricCard('Platform',    'v0.1 Online',                             Icons.verified,              _green,   1.0),
          ]),
        ),
      ),
      SliverPadding(padding: const EdgeInsets.symmetric(horizontal: 16),
          sliver: SliverToBoxAdapter(child: _ModuleGrid())),
      SliverPadding(padding: const EdgeInsets.all(16),
          sliver: SliverToBoxAdapter(child: _LogCard(logs: logs))),
    ]);
  }
}

class _MetricCard extends StatelessWidget {
  const _MetricCard(this.label, this.value, this.icon, this.color, this.progress);
  final String label, value;
  final IconData icon;
  final Color color;
  final double progress;

  @override
  Widget build(BuildContext context) {
    return Card(child: Padding(padding: const EdgeInsets.all(14), child: Column(
      crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Icon(icon, color: color, size: 18),
          const SizedBox(width: 6),
          Text(label, style: const TextStyle(fontSize: 12, color: Colors.white54)),
        ]),
        const Spacer(),
        Text(value, style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color)),
        const SizedBox(height: 8),
        ClipRRect(borderRadius: BorderRadius.circular(4), child: LinearProgressIndicator(
          value: progress.clamp(0.0, 1.0), minHeight: 4,
          backgroundColor: Colors.white12, color: color)),
      ],
    )));
  }
}

class _ModuleGrid extends StatelessWidget {
  static const _modules = [
    ('World Core',       Icons.public,                     1.0),
    ('City Builder',     Icons.location_city,              0.87),
    ('Vehicle Builder',  Icons.directions_car,             0.82),
    ('Character Studio', Icons.groups,                     0.79),
    ('Robot Factory',    Icons.precision_manufacturing,    0.74),
    ('3D Studio',        Icons.view_in_ar,                 0.82),
    ('Game Runtime',     Icons.sports_esports,             0.74),
    ('Reality Physics',  Icons.science,                    0.68),
  ];

  @override
  Widget build(BuildContext context) {
    return Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(
      crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('Platform Modules',
            style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white70)),
        const SizedBox(height: 12),
        ..._modules.map((m) => Padding(padding: const EdgeInsets.only(bottom: 8),
          child: Row(children: [
            Icon(m.$2, size: 16, color: _accent),
            const SizedBox(width: 8),
            Expanded(child: Text(m.$1, style: const TextStyle(fontSize: 13))),
            Text('${(m.$3*100).toStringAsFixed(0)}%',
                style: const TextStyle(fontSize: 12, color: Colors.white54)),
            const SizedBox(width: 8),
            SizedBox(width: 80, child: ClipRRect(borderRadius: BorderRadius.circular(3),
              child: LinearProgressIndicator(value: m.$3, minHeight: 4,
                  backgroundColor: Colors.white12, color: _accent))),
          ]))),
      ],
    )));
  }
}

class _LogCard extends StatelessWidget {
  const _LogCard({required this.logs});
  final List<LogEntry> logs;

  Color _col(String l) =>
      l == 'success' ? _green : l == 'warn' ? _orange : l == 'error' ? _red : Colors.white54;

  @override
  Widget build(BuildContext context) {
    return Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(
      crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('Event Log',
            style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white70)),
        const SizedBox(height: 8),
        ...logs.take(8).map((e) => Padding(padding: const EdgeInsets.only(bottom: 6),
          child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Container(width: 6, height: 6, margin: const EdgeInsets.only(top: 4, right: 8),
                decoration: BoxDecoration(shape: BoxShape.circle, color: _col(e.level))),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(e.title, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
              Text(e.detail, style: const TextStyle(fontSize: 11, color: Colors.white38)),
            ])),
          ]))),
      ],
    )));
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 2. CITY BUILDER
// ─────────────────────────────────────────────────────────────────────────────

class _CityScreen extends StatelessWidget {
  const _CityScreen({required this.vehicles, required this.cityHealth,
    required this.weather, required this.congestion, required this.roadworks,
    required this.running, required this.tick, required this.onToggle});
  final List<Vehicle> vehicles;
  final double cityHealth, congestion;
  final String weather;
  final int roadworks, tick;
  final bool running;
  final VoidCallback onToggle;

  @override
  Widget build(BuildContext context) {
    return CustomScrollView(slivers: [
      SliverAppBar(pinned: true, backgroundColor: _bg,
        title: const Text('City Builder Studio'),
        actions: [Padding(padding: const EdgeInsets.only(right: 12),
          child: FilledButton.icon(
            onPressed: onToggle,
            icon: Icon(running ? Icons.stop : Icons.play_arrow, size: 18),
            label: Text(running ? 'Stop' : 'Simulate'),
            style: FilledButton.styleFrom(backgroundColor: running ? _red : _green)))]),
      SliverPadding(padding: const EdgeInsets.all(16), sliver: SliverToBoxAdapter(
        child: Column(children: [
          Row(children: [
            Expanded(child: _StatChip('City Health', '${(cityHealth*100).toStringAsFixed(1)}%', _green)),
            const SizedBox(width: 8),
            Expanded(child: _StatChip('Congestion', '${(congestion*100).toStringAsFixed(0)}%', _orange)),
            const SizedBox(width: 8),
            Expanded(child: _StatChip('Weather', weather, _accent2)),
          ]),
          const SizedBox(height: 8),
          Row(children: [
            Expanded(child: _StatChip('Vehicles', '${vehicles.length}', _accent)),
            const SizedBox(width: 8),
            Expanded(child: _StatChip('Roadworks', '$roadworks zones', _yellow)),
            const SizedBox(width: 8),
            Expanded(child: _StatChip('Tick', '$tick', Colors.white54)),
          ]),
          const SizedBox(height: 16),
          Card(child: SizedBox(height: 260,
            child: ClipRRect(borderRadius: BorderRadius.circular(20),
              child: CustomPaint(
                  painter: _CityPainter(vehicles: vehicles, congestion: congestion))))),
          const SizedBox(height: 16),
          Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(
            crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('Traffic Lights',
                  style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white70)),
              const SizedBox(height: 12),
              Row(mainAxisAlignment: MainAxisAlignment.spaceEvenly, children: [
                _TrafficLight('North', congestion < 0.3 ? 'green' : congestion < 0.6 ? 'yellow' : 'red'),
                _TrafficLight('South', congestion < 0.4 ? 'green' : 'red'),
                _TrafficLight('East',  congestion < 0.5 ? 'green' : 'yellow'),
                _TrafficLight('West',  congestion < 0.2 ? 'green' : congestion < 0.7 ? 'yellow' : 'red'),
              ]),
            ],
          ))),
          const SizedBox(height: 16),
          Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(
            crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('Active Vehicles (${vehicles.length})',
                  style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white70)),
              const SizedBox(height: 8),
              ...vehicles.take(6).map((v) => Padding(padding: const EdgeInsets.only(bottom: 6),
                child: Row(children: [
                  Icon(v.type == 'truck' ? Icons.local_shipping
                      : v.type == 'bus' ? Icons.directions_bus : Icons.directions_car,
                      size: 16, color: _accent),
                  const SizedBox(width: 8),
                  Text(v.id, style: const TextStyle(fontSize: 12)),
                  const Spacer(),
                  Text('(${v.x.toStringAsFixed(0)},${v.z.toStringAsFixed(0)})',
                      style: const TextStyle(fontSize: 11, color: Colors.white38)),
                  const SizedBox(width: 8),
                  Text('${(v.speed*60).toStringAsFixed(0)} km/h',
                      style: const TextStyle(fontSize: 11, color: _accent2)),
                ]))),
            ],
          ))),
        ]),
      )),
    ]);
  }
}

class _StatChip extends StatelessWidget {
  const _StatChip(this.label, this.value, this.color);
  final String label, value;
  final Color color;
  @override
  Widget build(BuildContext context) => Card(child: Padding(
    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
    child: Column(children: [
      Text(label, style: const TextStyle(fontSize: 10, color: Colors.white38)),
      const SizedBox(height: 4),
      Text(value, style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: color)),
    ]),
  ));
}

class _TrafficLight extends StatelessWidget {
  const _TrafficLight(this.dir, this.state);
  final String dir, state;
  @override
  Widget build(BuildContext context) => Column(children: [
    Text(dir, style: const TextStyle(fontSize: 10, color: Colors.white38)),
    const SizedBox(height: 4),
    Container(width: 18, height: 18, decoration: BoxDecoration(
      shape: BoxShape.circle,
      color: state == 'green' ? _green : state == 'yellow' ? _yellow : _red,
      boxShadow: [BoxShadow(
        color: (state == 'green' ? _green : state == 'yellow' ? _yellow : _red)
            .withValues(alpha: 0.6),
        blurRadius: 8)],
    )),
  ]);
}

class _CityPainter extends CustomPainter {
  const _CityPainter({required this.vehicles, required this.congestion});
  final List<Vehicle> vehicles;
  final double congestion;

  @override
  void paint(Canvas canvas, Size size) {
    canvas.drawRect(Offset.zero & size, Paint()..color = const Color(0xFF0D1117));
    final road = Paint()..color = const Color(0xFF1E2533)..strokeWidth = 10;
    for (int i = 1; i < 4; i++) {
      canvas.drawLine(Offset(size.width*i/4, 0), Offset(size.width*i/4, size.height), road);
      canvas.drawLine(Offset(0, size.height*i/4), Offset(size.width, size.height*i/4), road);
    }
    final bld = Paint()..color = const Color(0xFF1A2340);
    final rng = math.Random(42);
    for (int i = 0; i < 20; i++) {
      canvas.drawRect(Rect.fromLTWH(
        rng.nextDouble()*size.width*0.85, rng.nextDouble()*size.height*0.85,
        12+rng.nextDouble()*20, 18+rng.nextDouble()*40), bld);
    }
    for (final v in vehicles) {
      final col = v.type == 'truck' ? _orange : v.type == 'bus' ? _yellow : _accent2;
      canvas.drawCircle(
          Offset(v.x/32*size.width, v.z/32*size.height), 4, Paint()..color = col);
    }
    if (congestion > 0.5) {
      canvas.drawRect(Offset.zero & size,
          Paint()..color = _red.withValues(alpha: (congestion-0.5)*0.3));
    }
  }

  @override
  bool shouldRepaint(_CityPainter _) => true;
}

// ─────────────────────────────────────────────────────────────────────────────
// 3. CAR BUILDER
// ─────────────────────────────────────────────────────────────────────────────

class _CarScreen extends StatelessWidget {
  const _CarScreen({required this.parts, required this.suspension,
    required this.drag, required this.downforce, required this.zero100,
    required this.braking, required this.onTune});
  final List<CarPart> parts;
  final String suspension;
  final double drag, downforce, zero100, braking;
  final VoidCallback onTune;

  double get _totalMass => parts.fold(0, (s, p) => s + p.mass);

  @override
  Widget build(BuildContext context) {
    return CustomScrollView(slivers: [
      SliverAppBar(pinned: true, backgroundColor: _bg,
        title: const Text('Car Builder Studio'),
        actions: [Padding(padding: const EdgeInsets.only(right: 12),
          child: FilledButton.icon(onPressed: onTune,
            icon: const Icon(Icons.tune, size: 18), label: const Text('Tune'),
            style: FilledButton.styleFrom(backgroundColor: _accent)))]),
      SliverPadding(padding: const EdgeInsets.all(16), sliver: SliverToBoxAdapter(
        child: Column(children: [
          Card(child: SizedBox(height: 180, child: CustomPaint(painter: _CarPainter()))),
          const SizedBox(height: 16),
          Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(
            crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('Physics Report',
                  style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white70)),
              const SizedBox(height: 12),
              _PhysRow('Total Mass',  '${_totalMass.toStringAsFixed(0)} kg', Icons.scale),
              _PhysRow('Drag Coeff',  drag.toStringAsFixed(3),               Icons.air),
              _PhysRow('Downforce',   downforce.toStringAsFixed(3),          Icons.arrow_downward),
              _PhysRow('0–100 km/h',  '${zero100.toStringAsFixed(1)} s',     Icons.speed),
              _PhysRow('Brake 100→0', '${braking.toStringAsFixed(1)} m',     Icons.stop_circle),
              _PhysRow('Suspension',  suspension,                            Icons.settings),
            ],
          ))),
          const SizedBox(height: 16),
          Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(
            crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('Components',
                  style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white70)),
              const SizedBox(height: 8),
              ...parts.map((p) => _PartRow(p)),
            ],
          ))),
        ]),
      )),
    ]);
  }
}

class _PhysRow extends StatelessWidget {
  const _PhysRow(this.label, this.value, this.icon);
  final String label, value;
  final IconData icon;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 10),
    child: Row(children: [
      Icon(icon, size: 15, color: _accent), const SizedBox(width: 8),
      Expanded(child: Text(label, style: const TextStyle(fontSize: 13, color: Colors.white70))),
      Text(value, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: _accent2)),
    ]));
}

class _PartRow extends StatelessWidget {
  const _PartRow(this.part);
  final CarPart part;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 8),
    child: Row(children: [
      Container(width: 8, height: 8, margin: const EdgeInsets.only(right: 10),
          decoration: const BoxDecoration(shape: BoxShape.circle, color: _accent)),
      Expanded(child: Text(part.name, style: const TextStyle(fontSize: 13))),
      Text(part.slot, style: const TextStyle(fontSize: 11, color: Colors.white38)),
      const SizedBox(width: 12),
      Text('${part.mass.toStringAsFixed(0)} kg',
          style: const TextStyle(fontSize: 12, color: _accent2)),
    ]));
}

class _CarPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final cx = size.width/2, cy = size.height/2;
    canvas.drawRRect(RRect.fromRectAndRadius(
        Rect.fromCenter(center: Offset(cx, cy), width: 160, height: 60),
        const Radius.circular(14)), Paint()..color = _accent);
    canvas.drawRRect(RRect.fromRectAndRadius(
        Rect.fromCenter(center: Offset(cx, cy-28), width: 90, height: 36),
        const Radius.circular(12)), Paint()..color = const Color(0xFF5A3FCC));
    final wheel = Paint()..color = const Color(0xFF1A1A2E);
    final rim   = Paint()..color = Colors.white30..style = PaintingStyle.stroke..strokeWidth = 2;
    for (final pos in [Offset(cx-52, cy+22), Offset(cx+52, cy+22)]) {
      canvas.drawCircle(pos, 18, wheel);
      canvas.drawCircle(pos, 12, rim);
    }
    canvas.drawCircle(Offset(cx+72, cy-8), 6, Paint()..color = _yellow);
    canvas.drawCircle(Offset(cx-72, cy-8), 6, Paint()..color = _yellow.withValues(alpha: 0.4));
    canvas.drawLine(Offset(cx-80, cy-30), Offset(cx+80, cy-30),
        Paint()..color = _accent2..strokeWidth = 2..strokeCap = StrokeCap.round);
  }
  @override
  bool shouldRepaint(_) => false;
}

// ─────────────────────────────────────────────────────────────────────────────
// 4. CHARACTER STUDIO
// ─────────────────────────────────────────────────────────────────────────────

class _CharacterScreen extends StatelessWidget {
  const _CharacterScreen({required this.chars, required this.filter, required this.onFilter});
  final List<MpcCharacter> chars;
  final String filter;
  final ValueChanged<String> onFilter;

  static const _categories = [
    'All','classic_city','tech_city','industrial','wasteland','coastal','sky_city','rural','metro',
  ];

  @override
  Widget build(BuildContext context) {
    final filtered = filter == 'All' ? chars : chars.where((c) => c.category == filter).toList();
    return CustomScrollView(slivers: [
      SliverAppBar(
        pinned: true, backgroundColor: _bg,
        title: const Text('Character Studio'),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(56),
          child: SizedBox(height: 48, child: ListView.builder(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            itemCount: _categories.length,
            itemBuilder: (_, i) => Padding(padding: const EdgeInsets.only(right: 8),
              child: FilterChip(
                label: Text(_categories[i], style: const TextStyle(fontSize: 12)),
                selected: filter == _categories[i],
                onSelected: (_) => onFilter(_categories[i]),
                selectedColor: _accent.withValues(alpha: 0.3),
                checkmarkColor: _accent))))),
      ),
      SliverPadding(
        padding: const EdgeInsets.all(16),
        sliver: SliverGrid(
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2, mainAxisSpacing: 12, crossAxisSpacing: 12, childAspectRatio: 1.1),
          delegate: SliverChildBuilderDelegate(
            (_, i) => _CharCard(filtered[i]), childCount: filtered.length),
        ),
      ),
    ]);
  }
}

class _CharCard extends StatelessWidget {
  const _CharCard(this.char);
  final MpcCharacter char;

  static const _roleColors = {
    'Guard': _red, 'Merchant': _yellow, 'Engineer': _accent2,
    'Medic': _green, 'Enforcer': _red, 'Hacker': _accent,
    'Navigator': _accent2, 'Pilot': _accent, 'Worker': Colors.white54,
    'Spy': _orange, 'Farmer': _green, 'Scavenger': _orange,
  };

  @override
  Widget build(BuildContext context) {
    final col = _roleColors[char.role] ?? Colors.white70;
    return Card(child: Padding(padding: const EdgeInsets.all(14), child: Column(
      crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          CircleAvatar(radius: 18,
            backgroundColor: col.withValues(alpha: 0.15),
            child: Text(char.name[0], style: TextStyle(color: col, fontWeight: FontWeight.bold))),
          const Spacer(),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            decoration: BoxDecoration(
                color: col.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(20)),
            child: Text(char.role, style: TextStyle(fontSize: 10, color: col))),
        ]),
        const SizedBox(height: 10),
        Text(char.name, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
        Text(char.category, style: const TextStyle(fontSize: 11, color: Colors.white38)),
        const Spacer(),
        Row(children: [
          const Icon(Icons.star, size: 13, color: _yellow),
          const SizedBox(width: 4),
          Text('Lv ${char.level}', style: const TextStyle(fontSize: 12, color: Colors.white54)),
        ]),
      ],
    )));
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 5. ROBOT FACTORY
// ─────────────────────────────────────────────────────────────────────────────

class _RobotScreen extends StatelessWidget {
  const _RobotScreen({required this.parts, required this.assembled,
    required this.efficiency, required this.onAssemble, required this.onReset});
  final List<RobotComponent> parts;
  final bool assembled;
  final double efficiency;
  final VoidCallback onAssemble, onReset;

  @override
  Widget build(BuildContext context) {
    return CustomScrollView(slivers: [
      SliverAppBar(pinned: true, backgroundColor: _bg,
        title: const Text('Robot Factory Studio'),
        actions: [Padding(padding: const EdgeInsets.only(right: 12),
          child: assembled
            ? OutlinedButton.icon(onPressed: onReset,
                icon: const Icon(Icons.refresh, size: 16), label: const Text('Reset'))
            : FilledButton.icon(onPressed: onAssemble,
                icon: const Icon(Icons.build, size: 16), label: const Text('Assemble'),
                style: FilledButton.styleFrom(backgroundColor: _accent)))]),
      SliverPadding(padding: const EdgeInsets.all(16), sliver: SliverToBoxAdapter(
        child: Column(children: [
          Card(child: SizedBox(height: 220,
            child: CustomPaint(painter: _RobotPainter(assembled: assembled)))),
          const SizedBox(height: 16),
          if (assembled) ...[
            Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(
              crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('Assembly Report',
                    style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white70)),
                const SizedBox(height: 12),
                Row(children: [
                  const Text('Efficiency', style: TextStyle(color: Colors.white54)),
                  const Spacer(),
                  Text('${efficiency.toStringAsFixed(1)}%', style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: efficiency > 70 ? _green : efficiency > 40 ? _orange : _red)),
                ]),
                const SizedBox(height: 8),
                ClipRRect(borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: efficiency/100, minHeight: 8, backgroundColor: Colors.white12,
                    color: efficiency > 70 ? _green : efficiency > 40 ? _orange : _red)),
                const SizedBox(height: 12),
                const Text('Status: ✓ ASSEMBLED',
                    style: TextStyle(color: _green, fontWeight: FontWeight.bold)),
              ],
            ))),
            const SizedBox(height: 16),
          ],
          Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(
            crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('Components',
                  style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white70)),
              const SizedBox(height: 8),
              ...parts.map((p) => _RobotPartRow(p, assembled)),
            ],
          ))),
        ]),
      )),
    ]);
  }
}

class _RobotPartRow extends StatelessWidget {
  const _RobotPartRow(this.p, this.active);
  final RobotComponent p;
  final bool active;

  Color _typeColor() => p.type == 'CPU'       ? _accent
      : p.type == 'Actuator'  ? _accent2
      : p.type == 'Sensor'    ? _green
      : p.type == 'Power'     ? _yellow
      : Colors.white38;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 10),
    child: Row(children: [
      Container(width: 8, height: 8, margin: const EdgeInsets.only(right: 10),
          decoration: BoxDecoration(
              shape: BoxShape.circle, color: active ? _typeColor() : Colors.white24)),
      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(p.name, style: const TextStyle(fontSize: 13)),
        Text(p.type, style: TextStyle(fontSize: 11, color: _typeColor())),
      ])),
      if (p.power > 0) ...[
        Text('${(p.power/5*100).toStringAsFixed(0)}%',
            style: TextStyle(fontSize: 12, color: active ? _typeColor() : Colors.white38)),
        const SizedBox(width: 8),
        SizedBox(width: 60, child: ClipRRect(borderRadius: BorderRadius.circular(3),
          child: LinearProgressIndicator(value: p.power/5, minHeight: 4,
              backgroundColor: Colors.white12,
              color: active ? _typeColor() : Colors.white24))),
      ],
    ]));
}

class _RobotPainter extends CustomPainter {
  const _RobotPainter({required this.assembled});
  final bool assembled;

  @override
  void paint(Canvas canvas, Size size) {
    final cx = size.width/2, cy = size.height/2;
    final col = assembled ? _accent : Colors.white24;
    final p = Paint()..color = col;
    canvas.drawRRect(RRect.fromRectAndRadius(
        Rect.fromCenter(center: Offset(cx, cy-60), width: 44, height: 40),
        const Radius.circular(8)), p);
    canvas.drawCircle(Offset(cx-10, cy-62), 5,
        Paint()..color = assembled ? _accent2 : Colors.white24);
    canvas.drawCircle(Offset(cx+10, cy-62), 5,
        Paint()..color = assembled ? _accent2 : Colors.white24);
    canvas.drawRRect(RRect.fromRectAndRadius(
        Rect.fromCenter(center: Offset(cx, cy), width: 60, height: 70),
        const Radius.circular(10)), p);
    canvas.drawRRect(RRect.fromRectAndRadius(
        Rect.fromCenter(center: Offset(cx-48, cy-10), width: 20, height: 56),
        const Radius.circular(8)), Paint()..color = assembled ? _accent2 : Colors.white24);
    canvas.drawRRect(RRect.fromRectAndRadius(
        Rect.fromCenter(center: Offset(cx+48, cy-10), width: 20, height: 56),
        const Radius.circular(8)), Paint()..color = assembled ? _accent2 : Colors.white24);
    canvas.drawRRect(RRect.fromRectAndRadius(
        Rect.fromCenter(center: Offset(cx-18, cy+54), width: 20, height: 44),
        const Radius.circular(8)), p);
    canvas.drawRRect(RRect.fromRectAndRadius(
        Rect.fromCenter(center: Offset(cx+18, cy+54), width: 20, height: 44),
        const Radius.circular(8)), p);
    if (assembled) {
      canvas.drawCircle(Offset(cx, cy), 12,
          Paint()..color = _accent.withValues(alpha: 0.3));
      canvas.drawCircle(Offset(cx, cy), 6, Paint()..color = _accent);
    }
  }

  @override
  bool shouldRepaint(_RobotPainter o) => o.assembled != assembled;
}

// ─────────────────────────────────────────────────────────────────────────────
// 6. 3-D STUDIO
// ─────────────────────────────────────────────────────────────────────────────

class _StudioScreen extends StatelessWidget {
  const _StudioScreen({
    required this.pulse, required this.tool, required this.material,
    required this.brushSize, required this.physicsRunning, required this.logs,
    required this.tools, required this.materials,
    required this.onTool, required this.onMaterial,
    required this.onBrush, required this.onPhysics,
  });
  final AnimationController pulse;
  final String tool, material;
  final double brushSize;
  final bool physicsRunning;
  final List<LogEntry> logs;
  final List<String> tools, materials;
  final ValueChanged<String> onTool, onMaterial;
  final ValueChanged<double> onBrush;
  final VoidCallback onPhysics;

  @override
  Widget build(BuildContext context) {
    return CustomScrollView(slivers: [
      SliverAppBar(pinned: true, backgroundColor: _bg,
        title: const Text('3D Voxel Studio'),
        actions: [Padding(padding: const EdgeInsets.only(right: 12),
          child: FilledButton.icon(
            onPressed: onPhysics,
            icon: Icon(physicsRunning ? Icons.pause : Icons.science, size: 18),
            label: Text(physicsRunning ? 'Pause' : 'Run Sim'),
            style: FilledButton.styleFrom(
                backgroundColor: physicsRunning ? _orange : _accent)))]),
      SliverPadding(padding: const EdgeInsets.all(16), sliver: SliverToBoxAdapter(
        child: Column(children: [
          Card(child: SizedBox(height: 220,
            child: AnimatedBuilder(animation: pulse, builder: (_, __) =>
              CustomPaint(painter: _IsoPainter(pulse.value, physicsRunning))))),
          const SizedBox(height: 16),
          Card(child: Padding(padding: const EdgeInsets.all(14), child: Column(
            crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('Tools', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white70)),
              const SizedBox(height: 10),
              Wrap(spacing: 8, runSpacing: 8, children: tools.map((t) => ChoiceChip(
                label: Text(t, style: const TextStyle(fontSize: 12)),
                selected: tool == t,
                onSelected: (_) => onTool(t),
                selectedColor: _accent.withValues(alpha: 0.3),
                checkmarkColor: _accent,
              )).toList()),
            ],
          ))),
          const SizedBox(height: 12),
          Card(child: Padding(padding: const EdgeInsets.all(14), child: Column(
            crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('Materials', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white70)),
              const SizedBox(height: 10),
              Wrap(spacing: 8, runSpacing: 8, children: materials.map((m) => ChoiceChip(
                label: Text(m, style: const TextStyle(fontSize: 12)),
                selected: material == m,
                onSelected: (_) => onMaterial(m),
                selectedColor: _accent2.withValues(alpha: 0.25),
                checkmarkColor: _accent2,
              )).toList()),
            ],
          ))),
          const SizedBox(height: 12),
          Card(child: Padding(padding: const EdgeInsets.all(14), child: Column(
            crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                const Text('Brush Size',
                    style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white70)),
                const Spacer(),
                Text(brushSize.toStringAsFixed(1),
                    style: const TextStyle(color: _accent2, fontWeight: FontWeight.bold)),
              ]),
              Slider(value: brushSize, min: 0.5, max: 8, divisions: 15,
                  activeColor: _accent2, onChanged: onBrush),
            ],
          ))),
        ]),
      )),
    ]);
  }
}

class _IsoPainter extends CustomPainter {
  const _IsoPainter(this.pulse, this.physics);
  final double pulse;
  final bool physics;

  @override
  void paint(Canvas canvas, Size size) {
    canvas.drawRect(Offset.zero & size, Paint()..color = const Color(0xFF0D1117));
    final cx = size.width/2, cy = size.height*0.6;
    const rows = 5, cols = 7, tw = 36.0, th = 20.0;
    final rng = math.Random(99);
    for (int r = rows-1; r >= 0; r--) {
      for (int c = 0; c < cols; c++) {
        final px = cx + (c-r)*(tw/2);
        final py = cy + (c+r)*(th/2);
        final h  = (rng.nextDouble()*3).ceil()*18.0;
        _drawVoxel(canvas, px, py-h, tw, th, h, physics && rng.nextDouble()>0.7);
      }
    }
  }

  void _drawVoxel(Canvas c, double x, double y, double tw, double th, double h, bool glow) {
    final rng = math.Random(x.toInt()^y.toInt());
    final hue = rng.nextDouble();
    final top  = HSVColor.fromAHSV(1, hue*360, 0.4, 0.75).toColor();
    final side = HSVColor.fromAHSV(1, hue*360, 0.7, 0.35).toColor();
    final base = HSVColor.fromAHSV(1, hue*360, 0.6, 0.50).toColor();

    final topPath = Path()
      ..moveTo(x,       y)
      ..lineTo(x+tw/2,  y-th/2)
      ..lineTo(x+tw,    y)
      ..lineTo(x+tw/2,  y+th/2)
      ..close();
    c.drawPath(topPath, Paint()..color = glow ? top.withValues(alpha: 0.6+pulse*0.4) : top);

    final leftPath = Path()
      ..moveTo(x,      y)
      ..lineTo(x,      y+h)
      ..lineTo(x+tw/2, y+h+th/2)
      ..lineTo(x+tw/2, y+th/2)
      ..close();
    c.drawPath(leftPath, Paint()..color = side);

    final rightPath = Path()
      ..moveTo(x+tw/2, y+th/2)
      ..lineTo(x+tw/2, y+h+th/2)
      ..lineTo(x+tw,   y+h)
      ..lineTo(x+tw,   y)
      ..close();
    c.drawPath(rightPath, Paint()..color = base);

    if (glow) {
      c.drawPath(topPath, Paint()
        ..color = _accent.withValues(alpha: pulse*0.5)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 6));
    }
  }

  @override
  bool shouldRepaint(_IsoPainter o) => o.pulse != pulse || o.physics != physics;
}

// ─────────────────────────────────────────────────────────────────────────────
// 7. GAMES
// ─────────────────────────────────────────────────────────────────────────────

class _GamesScreen extends StatefulWidget {
  const _GamesScreen({required this.race, required this.onStartRace,
    required this.onBoost, required this.onResetRace});
  final RaceState race;
  final VoidCallback onStartRace, onResetRace;
  final ValueChanged<bool> onBoost;

  @override
  State<_GamesScreen> createState() => _GamesScreenState();
}

class _GamesScreenState extends State<_GamesScreen> {
  int _gameTab = 0;
  static const _tabs = ['Racing','Sandbox','Fluid','Arena','Colony'];

  @override
  Widget build(BuildContext context) {
    return CustomScrollView(slivers: [
      SliverAppBar(pinned: true, backgroundColor: _bg,
        title: const Text('Game Studio'),
        bottom: PreferredSize(preferredSize: const Size.fromHeight(50),
          child: SizedBox(height: 42, child: ListView.builder(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
            itemCount: _tabs.length,
            itemBuilder: (_, i) => Padding(padding: const EdgeInsets.only(right: 8),
              child: ChoiceChip(
                label: Text(_tabs[i]), selected: _gameTab == i,
                onSelected: (_) => setState(() => _gameTab = i),
                selectedColor: _accent.withValues(alpha: 0.3))))))),
      SliverPadding(padding: const EdgeInsets.all(16), sliver: SliverToBoxAdapter(
        child: _gameTab == 0
          ? _RaceGame(race: widget.race, onStart: widget.onStartRace,
              onBoost: widget.onBoost, onReset: widget.onResetRace)
          : _StaticGameCard(_tabs[_gameTab]),
      )),
    ]);
  }
}

class _RaceGame extends StatelessWidget {
  const _RaceGame({required this.race, required this.onStart,
    required this.onBoost, required this.onReset});
  final RaceState race;
  final VoidCallback onStart, onReset;
  final ValueChanged<bool> onBoost;

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      Card(child: SizedBox(height: 200, child: CustomPaint(painter: _TrackPainter(race)))),
      const SizedBox(height: 16),
      Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(children: [
        Row(children: [
          Expanded(child: _TelRow('Speed',  '${race.speed.toStringAsFixed(0)} km/h', Icons.speed, _accent2)),
          Expanded(child: _TelRow('Lap',    '${race.lap}/3',                         Icons.loop,  _accent)),
        ]),
        const SizedBox(height: 8),
        Row(children: [
          Expanded(child: _TelRow('Fuel',  '${race.fuel.toStringAsFixed(0)}%',        Icons.local_gas_station, _yellow)),
          Expanded(child: _TelRow('Tires', '${(race.tire*100).toStringAsFixed(0)}%',  Icons.circle,            _orange)),
        ]),
        const SizedBox(height: 8),
        Row(children: [
          Expanded(child: _TelRow('Grip',  '${(race.grip*100).toStringAsFixed(0)}%',  Icons.settings_input_component, _green)),
          Expanded(child: _TelRow('Dist',  race.position.toStringAsFixed(2),          Icons.place,             Colors.white54)),
        ]),
      ]))),
      const SizedBox(height: 16),
      Row(children: [
        Expanded(child: race.finished
          ? FilledButton.icon(onPressed: onReset, icon: const Icon(Icons.refresh),
              label: const Text('Restart'),
              style: FilledButton.styleFrom(backgroundColor: _accent))
          : FilledButton.icon(onPressed: onStart, icon: const Icon(Icons.play_arrow),
              label: const Text('Race!'),
              style: FilledButton.styleFrom(backgroundColor: _green))),
        if (!race.finished) ...[
          const SizedBox(width: 12),
          GestureDetector(
            onTapDown:   (_) => onBoost(true),
            onTapUp:     (_) => onBoost(false),
            onTapCancel: ()  => onBoost(false),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
              decoration: BoxDecoration(
                color: race.boost ? _red : _card,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: _red.withValues(alpha: 0.5)),
              ),
              child: Row(mainAxisSize: MainAxisSize.min, children: [
                Icon(Icons.bolt, color: race.boost ? Colors.white : _red),
                const SizedBox(width: 6),
                Text('BOOST',
                    style: TextStyle(fontWeight: FontWeight.bold,
                        color: race.boost ? Colors.white : _red)),
              ]),
            ),
          ),
        ],
      ]),
      if (race.finished) ...[
        const SizedBox(height: 16),
        Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(
          crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(race.lap >= 3 ? '🏆 Race Complete!' : '💥 Out of Fuel!',
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            Text('Laps: ${race.lap}/3  |  Ticks: ${race.tick}',
                style: const TextStyle(color: Colors.white54)),
          ],
        ))),
      ],
      if (race.events.isNotEmpty) ...[
        const SizedBox(height: 12),
        Card(child: Padding(padding: const EdgeInsets.all(14), child: Column(
          crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('Race Log',
                style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white70)),
            const SizedBox(height: 8),
            ...race.events.take(5).map((e) => Padding(
              padding: const EdgeInsets.only(bottom: 4),
              child: Text('• $e', style: const TextStyle(fontSize: 12, color: Colors.white70)))),
          ],
        ))),
      ],
    ]);
  }
}

class _TelRow extends StatelessWidget {
  const _TelRow(this.label, this.value, this.icon, this.color);
  final String label, value;
  final IconData icon;
  final Color color;
  @override
  Widget build(BuildContext context) => Row(children: [
    Icon(icon, size: 14, color: color), const SizedBox(width: 6),
    Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(label, style: const TextStyle(fontSize: 10, color: Colors.white38)),
      Text(value, style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: color)),
    ]),
  ]);
}

class _TrackPainter extends CustomPainter {
  const _TrackPainter(this.race);
  final RaceState race;

  @override
  void paint(Canvas canvas, Size size) {
    canvas.drawRect(Offset.zero & size, Paint()..color = const Color(0xFF0A0E1A));
    canvas.drawPath(
      Path()
        ..moveTo(size.width*0.15, size.height*0.5)
        ..cubicTo(size.width*0.15, size.height*0.1, size.width*0.5, size.height*0.1, size.width*0.85, size.height*0.5)
        ..cubicTo(size.width*0.85, size.height*0.9, size.width*0.5, size.height*0.9, size.width*0.15, size.height*0.5),
      Paint()..color = const Color(0xFF1E2533)..style = PaintingStyle.stroke..strokeWidth = 28,
    );
    final t  = race.position % 1.0;
    final a  = t * 2 * math.pi;
    final carX = size.width*0.5  + math.cos(a)*size.width*0.35;
    final carY = size.height*0.5 + math.sin(a)*size.height*0.38;
    canvas.drawCircle(Offset(carX, carY), 8,  Paint()..color = race.boost ? _red : _accent);
    canvas.drawCircle(Offset(carX, carY), 5,  Paint()..color = Colors.white);
    final barW = (race.speed/260).clamp(0.0,1.0)*size.width*0.8;
    canvas.drawRRect(RRect.fromRectAndRadius(
        Rect.fromLTWH(size.width*0.1, size.height-16, size.width*0.8, 8),
        const Radius.circular(4)), Paint()..color = Colors.white12);
    canvas.drawRRect(RRect.fromRectAndRadius(
        Rect.fromLTWH(size.width*0.1, size.height-16, barW, 8),
        const Radius.circular(4)), Paint()..color = race.boost ? _red : _accent2);
  }

  @override
  bool shouldRepaint(_TrackPainter _) => true;
}

class _StaticGameCard extends StatelessWidget {
  const _StaticGameCard(this.name);
  final String name;

  static const _info = {
    'Sandbox': ('Creative mode with snap-grid construction and simulation toggles.',
                'Build a structure, inject heat, then watch fracture risk climb.',
                Icons.foundation),
    'Fluid':   ('Route water through destructible voxel channels.',
                'Goal: move 40 units of water to the blue target zone.',
                Icons.water_drop),
    'Arena':   ('Small action mode with moving hazards and pickups.',
                'Goal: survive waves while the world changes around you.',
                Icons.directions_run),
    'Colony':  ('Spawn AI agents and give them resource tasks.',
                'Goal: keep energy, heat and structure stability balanced.',
                Icons.groups_3),
  };

  @override
  Widget build(BuildContext context) {
    final info = _info[name]!;
    return Card(child: Padding(padding: const EdgeInsets.all(24), child: Column(
      crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Icon(info.$3, size: 32, color: _accent),
          const SizedBox(width: 12),
          Text(name, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
        ]),
        const SizedBox(height: 16),
        Text(info.$1, style: const TextStyle(color: Colors.white70, height: 1.5)),
        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
              color: _accent.withValues(alpha: 0.08), borderRadius: BorderRadius.circular(12)),
          child: Row(children: [
            const Icon(Icons.flag, size: 16, color: _accent),
            const SizedBox(width: 8),
            Expanded(child: Text(info.$2,
                style: const TextStyle(fontSize: 13, color: _accent2))),
          ]),
        ),
        const SizedBox(height: 20),
        FilledButton.icon(
          onPressed: () {},
          icon: const Icon(Icons.play_arrow),
          label: const Text('Launch (coming soon)'),
          style: FilledButton.styleFrom(
              backgroundColor: _accent, minimumSize: const Size(double.infinity, 48)),
        ),
      ],
    )));
  }
}
