import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

void main() {
  runApp(const VoxForgeApp());
}

class VoxForgeApp extends StatelessWidget {
  const VoxForgeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'VoxForge Noctilith Studio',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: const Color(0xFF7C5CFF),
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF090B13),
        cardTheme: CardThemeData(
          color: const Color(0xFF151827),
          elevation: 0,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
        ),
      ),
      home: const VoxForgeShell(),
    );
  }
}

class VoxForgeShell extends StatefulWidget {
  const VoxForgeShell({super.key});

  @override
  State<VoxForgeShell> createState() => _VoxForgeShellState();
}

class _VoxForgeShellState extends State<VoxForgeShell> with SingleTickerProviderStateMixin {
  int selectedIndex = 0;
  int tick = 0;
  double waterVolume = 32.4;
  double heat = 0.28;
  double fractureRisk = 0.07;
  double aiSignal = 0.42;
  double brushSize = 2.0;
  String selectedMaterial = 'Photonic Alloy';
  String selectedTool = 'Voxel Brush';
  String selectedGame = 'Sandbox Builder';
  bool bridgeOnline = true;
  bool physicsRunning = false;

  late final AnimationController pulseController;

  final List<LogEntry> logs = <LogEntry>[
    const LogEntry('World created', 'MilestoneA seed=1337, chunk grid ready'),
    const LogEntry('Studio tools ready', 'brush, erase, paint, fluid, fracture and agent spawn'),
    const LogEntry('Noctilith merge', 'thermal, entropy, fracture and debris bridges available'),
  ];

  final List<ModuleInfo> modules = const <ModuleInfo>[
    ModuleInfo('World Core', 'chunks, voxels, save/load', Icons.public, 1.0),
    ModuleInfo('3D Studio', 'viewport, builder tools, material palette', Icons.view_in_ar, 0.82),
    ModuleInfo('Simulation', 'fluid, thermal, entropy, fracture', Icons.science, 1.0),
    ModuleInfo('Game Runtime', 'prepared modes, player loop, objectives', Icons.sports_esports, 0.74),
    ModuleInfo('Builder', 'snap grid, parts, prefabs', Icons.construction, 0.78),
    ModuleInfo('Graphics', 'animated painters, palettes, VFX hooks', Icons.auto_awesome, 0.70),
    ModuleInfo('Audio', 'soundboard hooks and starter WAV assets', Icons.graphic_eq, 0.62),
    ModuleInfo('Bridge', 'future Python/native/HTTP integration', Icons.hub, 0.58),
  ];

  final List<String> tools = const <String>[
    'Voxel Brush',
    'Eraser',
    'Material Paint',
    'Fluid Source',
    'Heat Injector',
    'Fracture Probe',
    'Agent Spawner',
    'Prefab Stamp',
  ];

  final List<String> materials = const <String>[
    'Photonic Alloy',
    'Stone',
    'Glass',
    'Water',
    'Lava',
    'Carbon Fiber',
    'Neon Circuit',
    'Reactive Foam',
  ];

  final List<GameTemplate> games = const <GameTemplate>[
    GameTemplate(
      'Sandbox Builder',
      'Creative mode with snap-grid construction and simulation toggles.',
      Icons.foundation,
      'Build a structure, inject heat, then watch fracture risk climb.',
    ),
    GameTemplate(
      'Fluid Puzzle',
      'Route water through destructible voxel channels.',
      Icons.water_drop,
      'Goal: move 40 units of water to the blue target zone.',
    ),
    GameTemplate(
      'Arena Runner',
      'Small starter action mode with moving hazards and pickups.',
      Icons.directions_run,
      'Goal: survive waves while the world changes around you.',
    ),
    GameTemplate(
      'Colony Agents',
      'Spawn AI agents and give them resource tasks.',
      Icons.groups_3,
      'Goal: keep energy, heat and structure stability balanced.',
    ),
  ];

  final List<AssetItem> assetItems = const <AssetItem>[
    AssetItem('Glow Grid', 'Animated CustomPainter grid background', Icons.grid_on),
    AssetItem('Voxel Blocks', 'Procedural isometric voxel blocks', Icons.view_in_ar),
    AssetItem('Heat Pulse', 'Orange-red animated thermal overlay', Icons.local_fire_department),
    AssetItem('Fluid Sweep', 'Blue wave overlay for water flow', Icons.water),
    AssetItem('Impact Click', 'Built-in system click + WAV placeholder', Icons.volume_up),
    AssetItem('Bridge Ping', 'Short starter WAV asset in assets/audio', Icons.sensors),
  ];

  @override
  void initState() {
    super.initState();
    pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1800),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    pulseController.dispose();
    super.dispose();
  }

  void appendLog(String title, String message) {
    setState(() {
      logs.insert(0, LogEntry(title, message));
      if (logs.length > 12) {
        logs.removeLast();
      }
    });
  }

  void runDemoTick() {
    setState(() {
      tick += 10;
      final double wave = math.sin(tick / 18.0);
      waterVolume = (waterVolume - 0.18 + wave * 0.03).clamp(18.0, 50.0).toDouble();
      heat = (heat + 0.025 + math.max(0, wave) * 0.01).clamp(0.0, 1.0).toDouble();
      fractureRisk = (fractureRisk + heat * 0.018).clamp(0.0, 1.0).toDouble();
      aiSignal = (aiSignal + 0.04 - fractureRisk * 0.01).clamp(0.0, 1.0).toDouble();
      logs.insert(
        0,
        LogEntry(
          'Tick $tick',
          'fluid=${waterVolume.toStringAsFixed(2)}, heat=${heat.toStringAsFixed(2)}, fracture=${fractureRisk.toStringAsFixed(2)}',
        ),
      );
      if (logs.length > 12) {
        logs.removeLast();
      }
    });
  }

  void addWater() {
    setState(() {
      waterVolume = (waterVolume + 4.5).clamp(0.0, 50.0).toDouble();
      logs.insert(0, LogEntry('Fluid source', 'Added water volume: ${waterVolume.toStringAsFixed(2)}'));
      if (logs.length > 12) logs.removeLast();
    });
  }

  void injectHeat() {
    setState(() {
      heat = (heat + 0.16).clamp(0.0, 1.0).toDouble();
      fractureRisk = (fractureRisk + 0.05).clamp(0.0, 1.0).toDouble();
      logs.insert(0, const LogEntry('Thermal spike', 'Lava cell diffused into material map'));
      if (logs.length > 12) logs.removeLast();
    });
  }

  void togglePhysics() {
    setState(() {
      physicsRunning = !physicsRunning;
      logs.insert(
        0,
        LogEntry(
          physicsRunning ? 'Physics started' : 'Physics paused',
          physicsRunning ? 'Simulation loop is now advancing from UI ticks' : 'World state frozen for editing',
        ),
      );
      if (logs.length > 12) logs.removeLast();
    });
  }

  void resetDemo() {
    setState(() {
      tick = 0;
      waterVolume = 32.4;
      heat = 0.28;
      fractureRisk = 0.07;
      aiSignal = 0.42;
      physicsRunning = false;
      bridgeOnline = true;
      selectedMaterial = 'Photonic Alloy';
      selectedTool = 'Voxel Brush';
      selectedGame = 'Sandbox Builder';
      brushSize = 2.0;
      logs
        ..clear()
        ..addAll(const <LogEntry>[
          LogEntry('World reset', 'MilestoneA seed=1337, baseline state restored'),
          LogEntry('Bridge check', 'Flutter shell ready for native/backend integration'),
        ]);
    });
  }

  @override
  Widget build(BuildContext context) {
    final bool wide = MediaQuery.of(context).size.width >= 860;
    final List<Widget> pages = <Widget>[
      DashboardScreen(
        tick: tick,
        waterVolume: waterVolume,
        heat: heat,
        fractureRisk: fractureRisk,
        aiSignal: aiSignal,
        modules: modules,
        logs: logs,
        bridgeOnline: bridgeOnline,
        physicsRunning: physicsRunning,
        onRunTick: runDemoTick,
        onAddWater: addWater,
        onInjectHeat: injectHeat,
        onReset: resetDemo,
      ),
      StudioScreen(
        tick: tick,
        pulse: pulseController,
        tools: tools,
        materials: materials,
        selectedTool: selectedTool,
        selectedMaterial: selectedMaterial,
        brushSize: brushSize,
        heat: heat,
        waterVolume: waterVolume,
        fractureRisk: fractureRisk,
        onToolChanged: (String value) => setState(() => selectedTool = value),
        onMaterialChanged: (String value) => setState(() => selectedMaterial = value),
        onBrushChanged: (double value) => setState(() => brushSize = value),
        onStamp: () => appendLog('Studio action', '$selectedTool used with $selectedMaterial / brush=${brushSize.toStringAsFixed(1)}'),
      ),
      GamesScreen(
        games: games,
        selectedGame: selectedGame,
        tick: tick,
        physicsRunning: physicsRunning,
        onGameChanged: (String value) => setState(() => selectedGame = value),
        onStart: () {
          HapticFeedback.mediumImpact();
          appendLog('Game template started', '$selectedGame loaded into prototype runtime');
        },
        onTogglePhysics: togglePhysics,
        onRunTick: runDemoTick,
      ),
      AssetsScreen(
        assetItems: assetItems,
        pulse: pulseController,
        onPlaySound: () async {
          await SystemSound.play(SystemSoundType.click);
          appendLog('Audio cue', 'Played built-in system click; WAV placeholders are in assets/audio');
        },
      ),
      BuildScreen(
        bridgeOnline: bridgeOnline,
        onToggleBridge: () => setState(() {
          bridgeOnline = !bridgeOnline;
          logs.insert(0, LogEntry('Bridge state', bridgeOnline ? 'Bridge marked online' : 'Bridge marked offline'));
          if (logs.length > 12) logs.removeLast();
        }),
      ),
    ];

    return Scaffold(
      body: SafeArea(
        child: wide
            ? Row(
                children: <Widget>[
                  NavigationRail(
                    selectedIndex: selectedIndex,
                    extended: MediaQuery.of(context).size.width >= 1100,
                    onDestinationSelected: (int value) => setState(() => selectedIndex = value),
                    destinations: const <NavigationRailDestination>[
                      NavigationRailDestination(icon: Icon(Icons.dashboard_outlined), selectedIcon: Icon(Icons.dashboard), label: Text('Dashboard')),
                      NavigationRailDestination(icon: Icon(Icons.view_in_ar_outlined), selectedIcon: Icon(Icons.view_in_ar), label: Text('Studio')),
                      NavigationRailDestination(icon: Icon(Icons.sports_esports_outlined), selectedIcon: Icon(Icons.sports_esports), label: Text('Games')),
                      NavigationRailDestination(icon: Icon(Icons.auto_awesome_outlined), selectedIcon: Icon(Icons.auto_awesome), label: Text('Assets')),
                      NavigationRailDestination(icon: Icon(Icons.android_outlined), selectedIcon: Icon(Icons.android), label: Text('Build')),
                    ],
                  ),
                  const VerticalDivider(width: 1),
                  Expanded(child: IndexedStack(index: selectedIndex, children: pages)),
                ],
              )
            : Column(
                children: <Widget>[
                  Expanded(child: IndexedStack(index: selectedIndex, children: pages)),
                  NavigationBar(
                    selectedIndex: selectedIndex,
                    onDestinationSelected: (int value) => setState(() => selectedIndex = value),
                    destinations: const <NavigationDestination>[
                      NavigationDestination(icon: Icon(Icons.dashboard_outlined), selectedIcon: Icon(Icons.dashboard), label: 'Home'),
                      NavigationDestination(icon: Icon(Icons.view_in_ar_outlined), selectedIcon: Icon(Icons.view_in_ar), label: 'Studio'),
                      NavigationDestination(icon: Icon(Icons.sports_esports_outlined), selectedIcon: Icon(Icons.sports_esports), label: 'Games'),
                      NavigationDestination(icon: Icon(Icons.auto_awesome_outlined), selectedIcon: Icon(Icons.auto_awesome), label: 'Assets'),
                      NavigationDestination(icon: Icon(Icons.android_outlined), selectedIcon: Icon(Icons.android), label: 'Build'),
                    ],
                  ),
                ],
              ),
      ),
    );
  }
}

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({
    required this.tick,
    required this.waterVolume,
    required this.heat,
    required this.fractureRisk,
    required this.aiSignal,
    required this.modules,
    required this.logs,
    required this.bridgeOnline,
    required this.physicsRunning,
    required this.onRunTick,
    required this.onAddWater,
    required this.onInjectHeat,
    required this.onReset,
    super.key,
  });

  final int tick;
  final double waterVolume;
  final double heat;
  final double fractureRisk;
  final double aiSignal;
  final List<ModuleInfo> modules;
  final List<LogEntry> logs;
  final bool bridgeOnline;
  final bool physicsRunning;
  final VoidCallback onRunTick;
  final VoidCallback onAddWater;
  final VoidCallback onInjectHeat;
  final VoidCallback onReset;

  @override
  Widget build(BuildContext context) {
    return CustomScrollView(
      slivers: <Widget>[
        SliverAppBar.large(
          pinned: true,
          backgroundColor: const Color(0xFF090B13).withOpacity(0.94),
          title: const Text('VoxForge / Noctilith'),
          actions: <Widget>[
            Padding(
              padding: const EdgeInsets.only(right: 12),
              child: StatusPill(
                label: bridgeOnline ? 'bridge ready' : 'offline',
                icon: bridgeOnline ? Icons.verified : Icons.error_outline,
              ),
            ),
          ],
        ),
        SliverPadding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 28),
          sliver: SliverList(
            delegate: SliverChildListDelegate(<Widget>[
              HeroPanel(
                tick: tick,
                waterVolume: waterVolume,
                heat: heat,
                fractureRisk: fractureRisk,
                aiSignal: aiSignal,
                physicsRunning: physicsRunning,
                onRunTick: onRunTick,
                onAddWater: onAddWater,
                onInjectHeat: onInjectHeat,
                onReset: onReset,
              ),
              const SizedBox(height: 14),
              const SectionTitle('Engine modules'),
              const SizedBox(height: 8),
              ModuleGrid(modules: modules),
              const SizedBox(height: 18),
              const SectionTitle('Mini world viewport'),
              const SizedBox(height: 8),
              VoxelViewportCard(
                tick: tick,
                waterVolume: waterVolume,
                heat: heat,
                fractureRisk: fractureRisk,
              ),
              const SizedBox(height: 18),
              const SectionTitle('Runtime event log'),
              const SizedBox(height: 8),
              RuntimeLog(logs: logs),
            ]),
          ),
        ),
      ],
    );
  }
}

class StudioScreen extends StatelessWidget {
  const StudioScreen({
    required this.tick,
    required this.pulse,
    required this.tools,
    required this.materials,
    required this.selectedTool,
    required this.selectedMaterial,
    required this.brushSize,
    required this.heat,
    required this.waterVolume,
    required this.fractureRisk,
    required this.onToolChanged,
    required this.onMaterialChanged,
    required this.onBrushChanged,
    required this.onStamp,
    super.key,
  });

  final int tick;
  final Animation<double> pulse;
  final List<String> tools;
  final List<String> materials;
  final String selectedTool;
  final String selectedMaterial;
  final double brushSize;
  final double heat;
  final double waterVolume;
  final double fractureRisk;
  final ValueChanged<String> onToolChanged;
  final ValueChanged<String> onMaterialChanged;
  final ValueChanged<double> onBrushChanged;
  final VoidCallback onStamp;

  @override
  Widget build(BuildContext context) {
    final bool wide = MediaQuery.of(context).size.width >= 900;
    final Widget viewportCard = StudioViewportCard(
      tick: tick,
      pulse: pulse,
      selectedMaterial: selectedMaterial,
      selectedTool: selectedTool,
      heat: heat,
      waterVolume: waterVolume,
      fractureRisk: fractureRisk,
    );
    final Widget panelCard = BuilderPanel(
      tools: tools,
      materials: materials,
      selectedTool: selectedTool,
      selectedMaterial: selectedMaterial,
      brushSize: brushSize,
      onToolChanged: onToolChanged,
      onMaterialChanged: onMaterialChanged,
      onBrushChanged: onBrushChanged,
      onStamp: onStamp,
    );

    return ScreenScaffold(
      title: '3D Editing Studio',
      subtitle: 'Procedural viewport, builder tools, material palette and future backend bridge.',
      child: wide
          ? Row(
              children: <Widget>[
                Expanded(flex: 3, child: viewportCard),
                const SizedBox(width: 14),
                Expanded(flex: 2, child: panelCard),
              ],
            )
          : Column(
              children: <Widget>[
                SizedBox(height: 420, child: viewportCard),
                const SizedBox(height: 14),
                SizedBox(height: 620, child: panelCard),
              ],
            ),
    );
  }
}

class GamesScreen extends StatelessWidget {
  const GamesScreen({
    required this.games,
    required this.selectedGame,
    required this.tick,
    required this.physicsRunning,
    required this.onGameChanged,
    required this.onStart,
    required this.onTogglePhysics,
    required this.onRunTick,
    super.key,
  });

  final List<GameTemplate> games;
  final String selectedGame;
  final int tick;
  final bool physicsRunning;
  final ValueChanged<String> onGameChanged;
  final VoidCallback onStart;
  final VoidCallback onTogglePhysics;
  final VoidCallback onRunTick;

  @override
  Widget build(BuildContext context) {
    return ScreenScaffold(
      title: 'Prepared Games',
      subtitle: 'Starter modes you can later connect to real world state and player controls.',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          LayoutBuilder(
            builder: (BuildContext context, BoxConstraints constraints) {
              final int columns = constraints.maxWidth > 960 ? 4 : constraints.maxWidth > 640 ? 2 : 1;
              return GridView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: games.length,
                gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: columns,
                  childAspectRatio: columns == 1 ? 2.4 : 1.22,
                  crossAxisSpacing: 12,
                  mainAxisSpacing: 12,
                ),
                itemBuilder: (BuildContext context, int index) {
                  final GameTemplate game = games[index];
                  return GameTemplateCard(
                    game: game,
                    selected: game.name == selectedGame,
                    onTap: () => onGameChanged(game.name),
                  );
                },
              );
            },
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Row(
                    children: <Widget>[
                      const Icon(Icons.play_circle),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          'Runtime control: $selectedGame',
                          style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
                        ),
                      ),
                      StatusPill(label: physicsRunning ? 'running' : 'paused', icon: physicsRunning ? Icons.motion_photos_on : Icons.pause_circle),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text('Tick $tick. This is still a Flutter-side starter loop; replace calls with Python/native/HTTP snapshots later.'),
                  const SizedBox(height: 14),
                  Wrap(
                    spacing: 10,
                    runSpacing: 10,
                    children: <Widget>[
                      FilledButton.icon(onPressed: onStart, icon: const Icon(Icons.rocket_launch), label: const Text('Load game')),
                      OutlinedButton.icon(onPressed: onTogglePhysics, icon: const Icon(Icons.settings_backup_restore), label: Text(physicsRunning ? 'Pause physics' : 'Start physics')),
                      OutlinedButton.icon(onPressed: onRunTick, icon: const Icon(Icons.fast_forward), label: const Text('Advance tick')),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class AssetsScreen extends StatelessWidget {
  const AssetsScreen({
    required this.assetItems,
    required this.pulse,
    required this.onPlaySound,
    super.key,
  });

  final List<AssetItem> assetItems;
  final Animation<double> pulse;
  final VoidCallback onPlaySound;

  @override
  Widget build(BuildContext context) {
    return ScreenScaffold(
      title: 'Graphics, Animation & Audio',
      subtitle: 'Small built-in art direction kit: procedural UI graphics, animation timeline and sound hooks.',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Card(
            child: SizedBox(
              height: 230,
              child: AnimatedBuilder(
                animation: pulse,
                builder: (BuildContext context, Widget? child) {
                  return CustomPaint(
                    painter: AssetShowcasePainter(pulse.value),
                    child: Padding(
                      padding: const EdgeInsets.all(20),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          Text('Procedural showcase', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900)),
                          const SizedBox(height: 8),
                          const Text('No external packages required. This uses Flutter CustomPainter animations.'),
                          const Spacer(),
                          Wrap(
                            spacing: 10,
                            children: <Widget>[
                              Chip(label: Text('pulse ${(pulse.value * 100).round()}%')),
                              const Chip(label: Text('glow grid')),
                              const Chip(label: Text('voxel VFX')),
                            ],
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
          ),
          const SizedBox(height: 16),
          LayoutBuilder(
            builder: (BuildContext context, BoxConstraints constraints) {
              final int columns = constraints.maxWidth > 980 ? 3 : constraints.maxWidth > 640 ? 2 : 1;
              return GridView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: assetItems.length,
                gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: columns,
                  childAspectRatio: columns == 1 ? 3.0 : 1.75,
                  crossAxisSpacing: 12,
                  mainAxisSpacing: 12,
                ),
                itemBuilder: (BuildContext context, int index) {
                  final AssetItem item = assetItems[index];
                  return AssetCard(item: item, onPlaySound: item.title.contains('Click') || item.title.contains('Ping') ? onPlaySound : null);
                },
              );
            },
          ),
          const SizedBox(height: 16),
          const InfoBox(
            title: 'Audio note',
            body: 'The app uses SystemSound for a no-dependency click. Real WAV placeholders are included in assets/audio; add a package like audioplayers later when you want full playback.',
            icon: Icons.info_outline,
          ),
        ],
      ),
    );
  }
}

class BuildScreen extends StatelessWidget {
  const BuildScreen({
    required this.bridgeOnline,
    required this.onToggleBridge,
    super.key,
  });

  final bool bridgeOnline;
  final VoidCallback onToggleBridge;

  @override
  Widget build(BuildContext context) {
    return ScreenScaffold(
      title: 'Build, Signing & Bridge',
      subtitle: 'Android signing templates, release notes and future engine-bridge plan.',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Row(
                    children: <Widget>[
                      const Icon(Icons.verified_user),
                      const SizedBox(width: 10),
                      Expanded(child: Text('Android release signing', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800))),
                    ],
                  ),
                  const SizedBox(height: 12),
                  const Text('This pack includes key.properties.example, Gradle signing fragment and scripts for generating an upload keystore. It intentionally does not include a real private production key.'),
                  const SizedBox(height: 12),
                  const CodeBox('''keytool -genkey -v -keystore ~/upload-keystore.jks \\\n  -keyalg RSA -keysize 2048 -validity 10000 -alias upload'''),
                ],
              ),
            ),
          ),
          const SizedBox(height: 14),
          InfoBox(
            title: bridgeOnline ? 'Bridge status: online placeholder' : 'Bridge status: offline placeholder',
            body: 'Later, this should call the Python engine through HTTP/WebSocket, platform channel, FFI, or a native library. For now the UI uses local mock state.',
            icon: Icons.hub,
            action: OutlinedButton.icon(onPressed: onToggleBridge, icon: const Icon(Icons.power_settings_new), label: const Text('Toggle bridge')),
          ),
          const SizedBox(height: 14),
          const InfoBox(
            title: 'Included source input',
            body: 'The original uploaded voxforge_noctilith_merged.zip is copied into source_input/ so the transfer pack contains both the Flutter shell and the Python prototype archive.',
            icon: Icons.archive,
          ),
        ],
      ),
    );
  }
}

class ScreenScaffold extends StatelessWidget {
  const ScreenScaffold({required this.title, required this.subtitle, required this.child, super.key});

  final String title;
  final String subtitle;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return CustomScrollView(
      slivers: <Widget>[
        SliverAppBar.large(
          pinned: true,
          backgroundColor: const Color(0xFF090B13).withOpacity(0.94),
          title: Text(title),
        ),
        SliverPadding(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 28),
          sliver: SliverList(
            delegate: SliverChildListDelegate(<Widget>[
              Text(subtitle, style: Theme.of(context).textTheme.bodyLarge?.copyWith(color: Colors.white70)),
              const SizedBox(height: 16),
              child,
            ]),
          ),
        ),
      ],
    );
  }
}

class HeroPanel extends StatelessWidget {
  const HeroPanel({
    required this.tick,
    required this.waterVolume,
    required this.heat,
    required this.fractureRisk,
    required this.aiSignal,
    required this.physicsRunning,
    required this.onRunTick,
    required this.onAddWater,
    required this.onInjectHeat,
    required this.onReset,
    super.key,
  });

  final int tick;
  final double waterVolume;
  final double heat;
  final double fractureRisk;
  final double aiSignal;
  final bool physicsRunning;
  final VoidCallback onRunTick;
  final VoidCallback onAddWater;
  final VoidCallback onInjectHeat;
  final VoidCallback onReset;

  @override
  Widget build(BuildContext context) {
    return Card(
      clipBehavior: Clip.antiAlias,
      child: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: <Color>[
              const Color(0xFF151827),
              Theme.of(context).colorScheme.primary.withOpacity(0.18),
            ],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Wrap(
                spacing: 10,
                runSpacing: 10,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: <Widget>[
                  Text('Prototype control deck', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900)),
                  StatusPill(label: physicsRunning ? 'physics running' : 'edit mode', icon: physicsRunning ? Icons.motion_photos_on : Icons.edit),
                  StatusPill(label: 'tick $tick', icon: Icons.timer),
                ],
              ),
              const SizedBox(height: 10),
              const Text('A portable Flutter starter app for VoxForge / Noctilith: world dashboard, 3D studio shell, game templates, graphics/animation/audio kit and Android signing templates.'),
              const SizedBox(height: 16),
              Wrap(
                spacing: 10,
                runSpacing: 10,
                children: <Widget>[
                  FilledButton.icon(onPressed: onRunTick, icon: const Icon(Icons.play_arrow), label: const Text('Run tick')),
                  OutlinedButton.icon(onPressed: onAddWater, icon: const Icon(Icons.water_drop), label: const Text('Add water')),
                  OutlinedButton.icon(onPressed: onInjectHeat, icon: const Icon(Icons.local_fire_department), label: const Text('Inject heat')),
                  TextButton.icon(onPressed: onReset, icon: const Icon(Icons.restart_alt), label: const Text('Reset')),
                ],
              ),
              const SizedBox(height: 18),
              LayoutBuilder(
                builder: (BuildContext context, BoxConstraints constraints) {
                  final bool compact = constraints.maxWidth < 720;
                  final List<Widget> cards = <Widget>[
                    MetricCard(label: 'Water', value: waterVolume / 50.0, valueText: waterVolume.toStringAsFixed(1), icon: Icons.water),
                    MetricCard(label: 'Heat', value: heat, valueText: heat.toStringAsFixed(2), icon: Icons.thermostat),
                    MetricCard(label: 'Fracture', value: fractureRisk, valueText: fractureRisk.toStringAsFixed(2), icon: Icons.crisis_alert),
                    MetricCard(label: 'AI signal', value: aiSignal, valueText: aiSignal.toStringAsFixed(2), icon: Icons.psychology),
                  ];
                  if (compact) {
                    return Column(children: cards.map((Widget child) => Padding(padding: const EdgeInsets.only(bottom: 8), child: child)).toList());
                  }
                  return Row(children: cards.map((Widget child) => Expanded(child: Padding(padding: const EdgeInsets.only(right: 8), child: child))).toList());
                },
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class MetricCard extends StatelessWidget {
  const MetricCard({required this.label, required this.value, required this.valueText, required this.icon, super.key});

  final String label;
  final double value;
  final String valueText;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.06),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: Colors.white.withOpacity(0.08)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(children: <Widget>[Icon(icon, size: 18), const SizedBox(width: 8), Text(label)]),
          const SizedBox(height: 8),
          Text(valueText, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),
          const SizedBox(height: 8),
          LinearProgressIndicator(value: value.clamp(0.0, 1.0)),
        ],
      ),
    );
  }
}

class ModuleGrid extends StatelessWidget {
  const ModuleGrid({required this.modules, super.key});

  final List<ModuleInfo> modules;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final int columns = constraints.maxWidth > 980 ? 4 : constraints.maxWidth > 650 ? 2 : 1;
        return GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: modules.length,
          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: columns,
            childAspectRatio: columns == 1 ? 3.2 : 1.85,
            crossAxisSpacing: 10,
            mainAxisSpacing: 10,
          ),
          itemBuilder: (BuildContext context, int index) => ModuleCard(info: modules[index]),
        );
      },
    );
  }
}

class ModuleCard extends StatelessWidget {
  const ModuleCard({required this.info, super.key});

  final ModuleInfo info;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(children: <Widget>[Icon(info.icon), const SizedBox(width: 10), Expanded(child: Text(info.name, style: const TextStyle(fontWeight: FontWeight.w800)))]),
            const SizedBox(height: 8),
            Text(info.description, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(color: Colors.white70)),
            const Spacer(),
            LinearProgressIndicator(value: info.readiness),
          ],
        ),
      ),
    );
  }
}

class VoxelViewportCard extends StatelessWidget {
  const VoxelViewportCard({required this.tick, required this.waterVolume, required this.heat, required this.fractureRisk, super.key});

  final int tick;
  final double waterVolume;
  final double heat;
  final double fractureRisk;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: SizedBox(
        height: 260,
        child: CustomPaint(
          painter: MiniWorldPainter(tick: tick, heat: heat, waterVolume: waterVolume, fractureRisk: fractureRisk),
          child: const Align(
            alignment: Alignment.bottomLeft,
            child: Padding(
              padding: EdgeInsets.all(14),
              child: StatusPill(label: 'procedural preview', icon: Icons.memory),
            ),
          ),
        ),
      ),
    );
  }
}

class StudioViewportCard extends StatelessWidget {
  const StudioViewportCard({
    required this.tick,
    required this.pulse,
    required this.selectedMaterial,
    required this.selectedTool,
    required this.heat,
    required this.waterVolume,
    required this.fractureRisk,
    super.key,
  });

  final int tick;
  final Animation<double> pulse;
  final String selectedMaterial;
  final String selectedTool;
  final double heat;
  final double waterVolume;
  final double fractureRisk;

  @override
  Widget build(BuildContext context) {
    return Card(
      clipBehavior: Clip.antiAlias,
      child: AnimatedBuilder(
        animation: pulse,
        builder: (BuildContext context, Widget? child) {
          return CustomPaint(
            painter: StudioViewportPainter(
              tick: tick,
              pulse: pulse.value,
              materialName: selectedMaterial,
              toolName: selectedTool,
              heat: heat,
              waterVolume: waterVolume,
              fractureRisk: fractureRisk,
            ),
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Row(
                    children: <Widget>[
                      const Icon(Icons.view_in_ar),
                      const SizedBox(width: 10),
                      Expanded(child: Text('Viewport: $selectedTool / $selectedMaterial', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900))),
                    ],
                  ),
                  const Spacer(),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: <Widget>[
                      Chip(label: Text('tick $tick')),
                      Chip(label: Text('heat ${heat.toStringAsFixed(2)}')),
                      Chip(label: Text('fracture ${fractureRisk.toStringAsFixed(2)}')),
                    ],
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}

class BuilderPanel extends StatelessWidget {
  const BuilderPanel({
    required this.tools,
    required this.materials,
    required this.selectedTool,
    required this.selectedMaterial,
    required this.brushSize,
    required this.onToolChanged,
    required this.onMaterialChanged,
    required this.onBrushChanged,
    required this.onStamp,
    super.key,
  });

  final List<String> tools;
  final List<String> materials;
  final String selectedTool;
  final String selectedMaterial;
  final double brushSize;
  final ValueChanged<String> onToolChanged;
  final ValueChanged<String> onMaterialChanged;
  final ValueChanged<double> onBrushChanged;
  final VoidCallback onStamp;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: ListView(
          children: <Widget>[
            Text('Builder tools', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),
            const SizedBox(height: 8),
            const Text('Starter editor controls. Hook these into real engine commands later.'),
            const SizedBox(height: 16),
            Text('Tool', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: tools.map((String tool) {
                return ChoiceChip(
                  label: Text(tool),
                  selected: selectedTool == tool,
                  onSelected: (_) => onToolChanged(tool),
                );
              }).toList(),
            ),
            const SizedBox(height: 18),
            Text('Material', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: materials.map((String material) {
                return ChoiceChip(
                  label: Text(material),
                  selected: selectedMaterial == material,
                  onSelected: (_) => onMaterialChanged(material),
                );
              }).toList(),
            ),
            const SizedBox(height: 18),
            Text('Brush size: ${brushSize.toStringAsFixed(1)}'),
            Slider(value: brushSize, min: 1.0, max: 8.0, divisions: 14, onChanged: onBrushChanged),
            const SizedBox(height: 12),
            FilledButton.icon(onPressed: onStamp, icon: const Icon(Icons.add_box), label: const Text('Apply editor command')),
            const SizedBox(height: 14),
            const InfoBox(
              title: 'Prepared creation tools',
              body: 'Brush, eraser, material paint, fluid source, heat injector, fracture probe, agent spawner and prefab stamp are represented in the UI and ready to be wired to engine commands.',
              icon: Icons.tips_and_updates,
            ),
          ],
        ),
      ),
    );
  }
}

class GameTemplateCard extends StatelessWidget {
  const GameTemplateCard({required this.game, required this.selected, required this.onTap, super.key});

  final GameTemplate game;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(24),
      onTap: onTap,
      child: Card(
        color: selected ? Theme.of(context).colorScheme.primary.withOpacity(0.22) : null,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Row(children: <Widget>[Icon(game.icon), const SizedBox(width: 10), Expanded(child: Text(game.name, style: const TextStyle(fontWeight: FontWeight.w900)))]),
              const SizedBox(height: 8),
              Text(game.description, maxLines: 3, overflow: TextOverflow.ellipsis, style: const TextStyle(color: Colors.white70)),
              const Spacer(),
              Text(game.objective, maxLines: 2, overflow: TextOverflow.ellipsis),
            ],
          ),
        ),
      ),
    );
  }
}

class AssetCard extends StatelessWidget {
  const AssetCard({required this.item, this.onPlaySound, super.key});

  final AssetItem item;
  final VoidCallback? onPlaySound;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(children: <Widget>[Icon(item.icon), const SizedBox(width: 10), Expanded(child: Text(item.title, style: const TextStyle(fontWeight: FontWeight.w900)))]),
            const SizedBox(height: 8),
            Text(item.description, maxLines: 3, overflow: TextOverflow.ellipsis, style: const TextStyle(color: Colors.white70)),
            const Spacer(),
            if (onPlaySound != null) OutlinedButton.icon(onPressed: onPlaySound, icon: const Icon(Icons.play_arrow), label: const Text('Play cue')),
          ],
        ),
      ),
    );
  }
}

class RuntimeLog extends StatelessWidget {
  const RuntimeLog({required this.logs, super.key});

  final List<LogEntry> logs;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: logs
              .map((LogEntry entry) => ListTile(
                    dense: true,
                    leading: const Icon(Icons.terminal),
                    title: Text(entry.title, style: const TextStyle(fontWeight: FontWeight.w800)),
                    subtitle: Text(entry.message),
                  ))
              .toList(),
        ),
      ),
    );
  }
}

class SectionTitle extends StatelessWidget {
  const SectionTitle(this.text, {super.key});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Text(text, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900));
  }
}

class StatusPill extends StatelessWidget {
  const StatusPill({required this.label, required this.icon, super.key});

  final String label;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.08),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: Colors.white.withOpacity(0.08)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[Icon(icon, size: 16), const SizedBox(width: 6), Text(label)],
      ),
    );
  }
}

class InfoBox extends StatelessWidget {
  const InfoBox({required this.title, required this.body, required this.icon, this.action, super.key});

  final String title;
  final String body;
  final IconData icon;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.055),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.white.withOpacity(0.08)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Icon(icon),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(title, style: const TextStyle(fontWeight: FontWeight.w900)),
                const SizedBox(height: 6),
                Text(body, style: const TextStyle(color: Colors.white70)),
                if (action != null) ...<Widget>[const SizedBox(height: 10), action!],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class CodeBox extends StatelessWidget {
  const CodeBox(this.text, {super.key});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.36),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.08)),
      ),
      child: Text(text, style: const TextStyle(fontFamily: 'monospace')),
    );
  }
}

class MiniWorldPainter extends CustomPainter {
  MiniWorldPainter({required this.tick, required this.heat, required this.waterVolume, required this.fractureRisk});

  final int tick;
  final double heat;
  final double waterVolume;
  final double fractureRisk;

  @override
  void paint(Canvas canvas, Size size) {
    final Paint bg = Paint()
      ..shader = const LinearGradient(
        colors: <Color>[Color(0xFF111426), Color(0xFF070913)],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      ).createShader(Offset.zero & size);
    canvas.drawRect(Offset.zero & size, bg);

    final double block = math.min(size.width / 11, 26);
    final Offset origin = Offset(size.width * 0.50, size.height * 0.30);
    final Paint line = Paint()
      ..color = Colors.white.withOpacity(0.08)
      ..style = PaintingStyle.stroke;

    for (int x = -5; x <= 5; x++) {
      for (int y = -3; y <= 3; y++) {
        final Offset p = iso(origin, x.toDouble(), y.toDouble(), 0, block);
        final Path diamond = Path()
          ..moveTo(p.dx, p.dy - block * 0.35)
          ..lineTo(p.dx + block * 0.72, p.dy)
          ..lineTo(p.dx, p.dy + block * 0.35)
          ..lineTo(p.dx - block * 0.72, p.dy)
          ..close();
        canvas.drawPath(diamond, line);
      }
    }

    final int count = 26;
    for (int i = 0; i < count; i++) {
      final int x = (i % 7) - 3;
      final int y = ((i * 3) % 7) - 3;
      final int z = 1 + ((i + tick ~/ 10) % 4);
      final double hot = (math.sin(i + tick / 12) + 1) * 0.5 * heat;
      final Color color = Color.lerp(const Color(0xFF4B6BFF), const Color(0xFFFF7A3D), hot)!.withOpacity(0.84);
      drawCube(canvas, iso(origin, x.toDouble(), y.toDouble(), z.toDouble(), block), block * 0.72, color);
    }

    final Paint water = Paint()..color = const Color(0xFF42C7FF).withOpacity((waterVolume / 60).clamp(0.20, 0.72));
    final double wave = math.sin(tick / 10) * 8;
    canvas.drawOval(Rect.fromCenter(center: Offset(size.width * 0.70, size.height * 0.72 + wave), width: 120, height: 34), water);

    final Paint risk = Paint()
      ..color = Colors.redAccent.withOpacity(fractureRisk.clamp(0.0, 0.7))
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;
    canvas.drawCircle(Offset(size.width * 0.28, size.height * 0.62), 32 + fractureRisk * 40, risk);
  }

  @override
  bool shouldRepaint(covariant MiniWorldPainter oldDelegate) {
    return oldDelegate.tick != tick || oldDelegate.heat != heat || oldDelegate.waterVolume != waterVolume || oldDelegate.fractureRisk != fractureRisk;
  }
}

class StudioViewportPainter extends CustomPainter {
  StudioViewportPainter({
    required this.tick,
    required this.pulse,
    required this.materialName,
    required this.toolName,
    required this.heat,
    required this.waterVolume,
    required this.fractureRisk,
  });

  final int tick;
  final double pulse;
  final String materialName;
  final String toolName;
  final double heat;
  final double waterVolume;
  final double fractureRisk;

  @override
  void paint(Canvas canvas, Size size) {
    final Paint bg = Paint()
      ..shader = RadialGradient(
        colors: <Color>[const Color(0xFF241B4D).withOpacity(0.55 + pulse * 0.12), const Color(0xFF090B13)],
      ).createShader(Offset.zero & size);
    canvas.drawRect(Offset.zero & size, bg);

    final double block = math.min(size.width, size.height) / 13;
    final Offset origin = Offset(size.width * 0.52, size.height * 0.42);
    final Paint grid = Paint()
      ..color = Colors.white.withOpacity(0.08)
      ..style = PaintingStyle.stroke;

    for (int x = -6; x <= 6; x++) {
      final Offset a = iso(origin, x.toDouble(), -5, 0, block);
      final Offset b = iso(origin, x.toDouble(), 5, 0, block);
      canvas.drawLine(a, b, grid);
    }
    for (int y = -5; y <= 5; y++) {
      final Offset a = iso(origin, -6, y.toDouble(), 0, block);
      final Offset b = iso(origin, 6, y.toDouble(), 0, block);
      canvas.drawLine(a, b, grid);
    }

    for (int i = 0; i < 34; i++) {
      final int x = (i % 8) - 4;
      final int y = ((i * 5) % 9) - 4;
      final int z = 1 + ((i * 7 + tick ~/ 10) % 5);
      final double blend = ((math.sin(i * 0.7 + pulse * math.pi) + 1) * 0.5).clamp(0.0, 1.0);
      final Color base = materialColor(materialName, blend);
      drawCube(canvas, iso(origin, x.toDouble(), y.toDouble(), z.toDouble(), block), block * 0.76, base.withOpacity(0.88));
    }

    final Paint cursor = Paint()
      ..color = Colors.white.withOpacity(0.80)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;
    final Offset c = Offset(size.width * (0.52 + math.sin(pulse * math.pi * 2) * 0.08), size.height * 0.42);
    canvas.drawCircle(c, 22 + pulse * 12, cursor);

    final Paint heatPaint = Paint()..color = Colors.deepOrangeAccent.withOpacity((heat * 0.28).clamp(0.0, 0.36));
    canvas.drawCircle(Offset(size.width * 0.80, size.height * 0.32), 70 + pulse * 20, heatPaint);

    final Paint fluid = Paint()..color = Colors.cyanAccent.withOpacity((waterVolume / 90).clamp(0.1, 0.46));
    canvas.drawRRect(RRect.fromRectAndRadius(Rect.fromLTWH(size.width * 0.08, size.height * 0.70, size.width * 0.38, 44), const Radius.circular(24)), fluid);

    final Paint risk = Paint()
      ..color = Colors.redAccent.withOpacity(fractureRisk.clamp(0.0, 0.70))
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.4;
    canvas.drawCircle(Offset(size.width * 0.34, size.height * 0.40), 36 + fractureRisk * 80, risk);
  }

  @override
  bool shouldRepaint(covariant StudioViewportPainter oldDelegate) {
    return oldDelegate.tick != tick || oldDelegate.pulse != pulse || oldDelegate.materialName != materialName || oldDelegate.toolName != toolName || oldDelegate.heat != heat || oldDelegate.waterVolume != waterVolume || oldDelegate.fractureRisk != fractureRisk;
  }
}

class AssetShowcasePainter extends CustomPainter {
  AssetShowcasePainter(this.pulse);

  final double pulse;

  @override
  void paint(Canvas canvas, Size size) {
    final Paint bg = Paint()
      ..shader = const LinearGradient(
        colors: <Color>[Color(0xFF101426), Color(0xFF25183D)],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      ).createShader(Offset.zero & size);
    canvas.drawRect(Offset.zero & size, bg);

    final Paint grid = Paint()
      ..color = Colors.white.withOpacity(0.06)
      ..strokeWidth = 1;
    for (double x = 0; x < size.width; x += 28) {
      canvas.drawLine(Offset(x, 0), Offset(x + 80, size.height), grid);
    }

    final Paint glow = Paint()..color = Colors.purpleAccent.withOpacity(0.24 + pulse * 0.16);
    canvas.drawCircle(Offset(size.width * 0.78, size.height * 0.40), 80 + pulse * 34, glow);
    final Paint water = Paint()..color = Colors.cyanAccent.withOpacity(0.18 + pulse * 0.12);
    canvas.drawOval(Rect.fromCenter(center: Offset(size.width * 0.68, size.height * 0.72), width: 180, height: 42), water);
  }

  @override
  bool shouldRepaint(covariant AssetShowcasePainter oldDelegate) => oldDelegate.pulse != pulse;
}

Offset iso(Offset origin, double x, double y, double z, double block) {
  return Offset(
    origin.dx + (x - y) * block * 0.72,
    origin.dy + (x + y) * block * 0.36 - z * block * 0.62,
  );
}

void drawCube(Canvas canvas, Offset top, double size, Color color) {
  final Paint topPaint = Paint()..color = Color.lerp(color, Colors.white, 0.18)!;
  final Paint leftPaint = Paint()..color = Color.lerp(color, Colors.black, 0.18)!;
  final Paint rightPaint = Paint()..color = Color.lerp(color, Colors.black, 0.34)!;
  final double h = size * 0.52;

  final Path topFace = Path()
    ..moveTo(top.dx, top.dy - h)
    ..lineTo(top.dx + size, top.dy)
    ..lineTo(top.dx, top.dy + h)
    ..lineTo(top.dx - size, top.dy)
    ..close();
  final Path leftFace = Path()
    ..moveTo(top.dx - size, top.dy)
    ..lineTo(top.dx, top.dy + h)
    ..lineTo(top.dx, top.dy + h + size)
    ..lineTo(top.dx - size, top.dy + size)
    ..close();
  final Path rightFace = Path()
    ..moveTo(top.dx + size, top.dy)
    ..lineTo(top.dx, top.dy + h)
    ..lineTo(top.dx, top.dy + h + size)
    ..lineTo(top.dx + size, top.dy + size)
    ..close();

  canvas.drawPath(leftFace, leftPaint);
  canvas.drawPath(rightFace, rightPaint);
  canvas.drawPath(topFace, topPaint);

  final Paint outline = Paint()
    ..color = Colors.white.withOpacity(0.10)
    ..style = PaintingStyle.stroke;
  canvas.drawPath(topFace, outline);
  canvas.drawPath(leftFace, outline);
  canvas.drawPath(rightFace, outline);
}

Color materialColor(String materialName, double blend) {
  switch (materialName) {
    case 'Stone':
      return Color.lerp(const Color(0xFF6C7080), const Color(0xFFB8BBC8), blend)!;
    case 'Glass':
      return Color.lerp(const Color(0xFF9EE7FF), const Color(0xFFE8FBFF), blend)!;
    case 'Water':
      return Color.lerp(const Color(0xFF176CFF), const Color(0xFF4EE4FF), blend)!;
    case 'Lava':
      return Color.lerp(const Color(0xFFFF3D2E), const Color(0xFFFFC14A), blend)!;
    case 'Carbon Fiber':
      return Color.lerp(const Color(0xFF16191F), const Color(0xFF596070), blend)!;
    case 'Neon Circuit':
      return Color.lerp(const Color(0xFF00FFC2), const Color(0xFFAE5CFF), blend)!;
    case 'Reactive Foam':
      return Color.lerp(const Color(0xFFECE0C9), const Color(0xFF8CFFE5), blend)!;
    case 'Photonic Alloy':
    default:
      return Color.lerp(const Color(0xFF7864FF), const Color(0xFF38D8FF), blend)!;
  }
}

class LogEntry {
  const LogEntry(this.title, this.message);
  final String title;
  final String message;
}

class ModuleInfo {
  const ModuleInfo(this.name, this.description, this.icon, this.readiness);
  final String name;
  final String description;
  final IconData icon;
  final double readiness;
}

class GameTemplate {
  const GameTemplate(this.name, this.description, this.icon, this.objective);
  final String name;
  final String description;
  final IconData icon;
  final String objective;
}

class AssetItem {
  const AssetItem(this.title, this.description, this.icon);
  final String title;
  final String description;
  final IconData icon;
}
