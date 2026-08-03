import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:just_audio/just_audio.dart';
import 'package:shared_preferences/shared_preferences.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final prefs = await SharedPreferences.getInstance();
  runApp(AcademyApp(prefs: prefs));
}

const _en = <String, String>{
  'title': 'Piano & Violin Academy',
  'welcome': 'Welcome back',
  'subtitle': 'Learn music step by step, completely offline.',
  'piano': 'Learn Piano',
  'violin': 'Learn Violin',
  'practice': 'Free Practice',
  'continue': 'Continue Learning',
  'progress': 'Progress',
  'settings': 'Settings',
  'lessons': 'Lessons',
  'about': 'About',
  'completed': 'Completed lessons',
  'best': 'Best practice score',
  'streak': 'Daily streak',
  'days': 'days',
  'language': 'Language',
  'theme': 'Theme',
  'system': 'System',
  'light': 'Light',
  'dark': 'Dark',
  'labels': 'Show note labels',
  'vibration': 'Vibration feedback',
  'reset': 'Reset progress',
  'start': 'Start lesson',
  'complete': 'Mark lesson complete',
  'demo': 'Play demo',
  'accuracy': 'Accuracy',
  'next': 'Next expected note',
  'volume': 'Volume',
  'metronome': 'Metronome',
  'bpm': 'BPM',
  'pianoIntro': 'Learn the keyboard, note names, rhythm, scales and chords.',
  'violinIntro': 'Learn strings, finger positions, bow direction and intonation.',
  'practiceIntro': 'Choose an instrument and test your timing and accuracy.',
};

const _ar = <String, String>{
  'title': 'أكاديمية البيانو والكمان',
  'welcome': 'مرحبًا بعودتك',
  'subtitle': 'تعلّم الموسيقى خطوة بخطوة دون إنترنت.',
  'piano': 'تعلّم البيانو',
  'violin': 'تعلّم الكمان',
  'practice': 'تدريب حر',
  'continue': 'متابعة التعلّم',
  'progress': 'التقدّم',
  'settings': 'الإعدادات',
  'lessons': 'الدروس',
  'about': 'حول التطبيق',
  'completed': 'الدروس المكتملة',
  'best': 'أفضل نتيجة تدريب',
  'streak': 'سلسلة التدريب اليومية',
  'days': 'أيام',
  'language': 'اللغة',
  'theme': 'المظهر',
  'system': 'النظام',
  'light': 'فاتح',
  'dark': 'داكن',
  'labels': 'إظهار أسماء النغمات',
  'vibration': 'اهتزاز عند العزف',
  'reset': 'تصفير التقدّم',
  'start': 'ابدأ الدرس',
  'complete': 'إكمال الدرس',
  'demo': 'تشغيل المثال',
  'accuracy': 'الدقة',
  'next': 'النغمة المطلوبة',
  'volume': 'الصوت',
  'metronome': 'المترونوم',
  'bpm': 'السرعة',
  'pianoIntro': 'تعلّم لوحة المفاتيح وأسماء النغمات والإيقاع والسلالم والتآلفات.',
  'violinIntro': 'تعلّم الأوتار ومواضع الأصابع واتجاه القوس وضبط النغمة.',
  'practiceIntro': 'اختر آلة واختبر دقتك وتوقيتك.',
};

class AcademyApp extends StatefulWidget {
  const AcademyApp({super.key, required this.prefs});
  final SharedPreferences prefs;

  @override
  State<AcademyApp> createState() => _AcademyAppState();
}

class _AcademyAppState extends State<AcademyApp> {
  late String language;
  late ThemeMode themeMode;
  late bool showLabels;
  late bool vibration;
  late int completedLessons;
  late int bestScore;
  late int streak;

  bool get isArabic => language == 'ar';
  String tr(String key) => (isArabic ? _ar : _en)[key] ?? key;

  @override
  void initState() {
    super.initState();
    language = widget.prefs.getString('language') ?? 'en';
    themeMode = ThemeMode.values.firstWhere(
      (mode) => mode.name == (widget.prefs.getString('theme') ?? 'system'),
      orElse: () => ThemeMode.system,
    );
    showLabels = widget.prefs.getBool('showLabels') ?? true;
    vibration = widget.prefs.getBool('vibration') ?? true;
    completedLessons = widget.prefs.getInt('completedLessons') ?? 0;
    bestScore = widget.prefs.getInt('bestScore') ?? 0;
    streak = widget.prefs.getInt('streak') ?? 0;
  }

  Future<void> updateSettings({
    String? language,
    ThemeMode? themeMode,
    bool? showLabels,
    bool? vibration,
  }) async {
    setState(() {
      this.language = language ?? this.language;
      this.themeMode = themeMode ?? this.themeMode;
      this.showLabels = showLabels ?? this.showLabels;
      this.vibration = vibration ?? this.vibration;
    });
    await widget.prefs.setString('language', this.language);
    await widget.prefs.setString('theme', this.themeMode.name);
    await widget.prefs.setBool('showLabels', this.showLabels);
    await widget.prefs.setBool('vibration', this.vibration);
  }

  Future<void> completeLesson() async {
    setState(() {
      completedLessons += 1;
      streak = streak == 0 ? 1 : streak;
    });
    await widget.prefs.setInt('completedLessons', completedLessons);
    await widget.prefs.setInt('streak', streak);
  }

  Future<void> saveScore(int score) async {
    if (score <= bestScore) return;
    setState(() => bestScore = score);
    await widget.prefs.setInt('bestScore', bestScore);
  }

  Future<void> resetProgress() async {
    setState(() {
      completedLessons = 0;
      bestScore = 0;
      streak = 0;
    });
    await widget.prefs.remove('completedLessons');
    await widget.prefs.remove('bestScore');
    await widget.prefs.remove('streak');
  }

  @override
  Widget build(BuildContext context) {
    final seed = const Color(0xff6d4aff);
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Piano & Violin Academy',
      themeMode: themeMode,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: seed),
      ),
      darkTheme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: seed,
          brightness: Brightness.dark,
        ),
      ),
      home: Directionality(
        textDirection: isArabic ? TextDirection.rtl : TextDirection.ltr,
        child: HomeScreen(
          tr: tr,
          isArabic: isArabic,
          showLabels: showLabels,
          vibration: vibration,
          completedLessons: completedLessons,
          bestScore: bestScore,
          streak: streak,
          onCompleteLesson: completeLesson,
          onSaveScore: saveScore,
          onSettingsChanged: updateSettings,
          onReset: resetProgress,
          language: language,
          themeMode: themeMode,
        ),
      ),
    );
  }
}

class HomeScreen extends StatelessWidget {
  const HomeScreen({
    super.key,
    required this.tr,
    required this.isArabic,
    required this.showLabels,
    required this.vibration,
    required this.completedLessons,
    required this.bestScore,
    required this.streak,
    required this.onCompleteLesson,
    required this.onSaveScore,
    required this.onSettingsChanged,
    required this.onReset,
    required this.language,
    required this.themeMode,
  });

  final String Function(String) tr;
  final bool isArabic;
  final bool showLabels;
  final bool vibration;
  final int completedLessons;
  final int bestScore;
  final int streak;
  final Future<void> Function() onCompleteLesson;
  final Future<void> Function(int) onSaveScore;
  final Future<void> Function({
    String? language,
    ThemeMode? themeMode,
    bool? showLabels,
    bool? vibration,
  }) onSettingsChanged;
  final Future<void> Function() onReset;
  final String language;
  final ThemeMode themeMode;

  void open(BuildContext context, Widget page) {
    Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => page));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(tr('title')),
        actions: [
          IconButton(
            tooltip: tr('progress'),
            onPressed: () => open(
              context,
              ProgressScreen(
                tr: tr,
                completed: completedLessons,
                best: bestScore,
                streak: streak,
              ),
            ),
            icon: const Icon(Icons.insights_rounded),
          ),
          IconButton(
            tooltip: tr('settings'),
            onPressed: () => open(
              context,
              SettingsScreen(
                tr: tr,
                language: language,
                themeMode: themeMode,
                showLabels: showLabels,
                vibration: vibration,
                onChanged: onSettingsChanged,
                onReset: onReset,
              ),
            ),
            icon: const Icon(Icons.settings_rounded),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text(tr('welcome'), style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 8),
          Text(tr('subtitle')),
          const SizedBox(height: 22),
          _FeatureCard(
            icon: Icons.piano_rounded,
            title: tr('piano'),
            subtitle: tr('pianoIntro'),
            onTap: () => open(
              context,
              PianoScreen(
                tr: tr,
                showLabels: showLabels,
                vibration: vibration,
              ),
            ),
          ),
          const SizedBox(height: 14),
          _FeatureCard(
            icon: Icons.music_note_rounded,
            title: tr('violin'),
            subtitle: tr('violinIntro'),
            onTap: () => open(
              context,
              ViolinScreen(
                tr: tr,
                showLabels: showLabels,
                vibration: vibration,
              ),
            ),
          ),
          const SizedBox(height: 14),
          _FeatureCard(
            icon: Icons.school_rounded,
            title: tr('lessons'),
            subtitle: tr('continue'),
            onTap: () => open(
              context,
              LessonsScreen(
                tr: tr,
                showLabels: showLabels,
                vibration: vibration,
                onComplete: onCompleteLesson,
              ),
            ),
          ),
          const SizedBox(height: 14),
          _FeatureCard(
            icon: Icons.track_changes_rounded,
            title: tr('practice'),
            subtitle: tr('practiceIntro'),
            onTap: () => open(
              context,
              PracticeScreen(
                tr: tr,
                vibration: vibration,
                onSaveScore: onSaveScore,
              ),
            ),
          ),
          const SizedBox(height: 24),
          Row(
            children: [
              Expanded(child: _Metric(value: '$completedLessons', label: tr('completed'))),
              const SizedBox(width: 10),
              Expanded(child: _Metric(value: '$bestScore%', label: tr('best'))),
              const SizedBox(width: 10),
              Expanded(child: _Metric(value: '$streak', label: tr('streak'))),
            ],
          ),
        ],
      ),
    );
  }
}

class _FeatureCard extends StatelessWidget {
  const _FeatureCard({required this.icon, required this.title, required this.subtitle, required this.onTap});
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Row(
            children: [
              CircleAvatar(radius: 28, child: Icon(icon, size: 30)),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: Theme.of(context).textTheme.titleLarge),
                    const SizedBox(height: 5),
                    Text(subtitle),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right_rounded),
            ],
          ),
        ),
      ),
    );
  }
}

class _Metric extends StatelessWidget {
  const _Metric({required this.value, required this.label});
  final String value;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            Text(value, style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 4),
            Text(label, textAlign: TextAlign.center, maxLines: 2),
          ],
        ),
      ),
    );
  }
}

class NotePlayer {
  final Map<String, AudioPlayer> _players = <String, AudioPlayer>{};

  Future<void> play(String note, double volume) async {
    final player = _players.putIfAbsent(note, AudioPlayer.new);
    if (player.audioSource == null) {
      await player.setAsset('assets/audio/$note.wav');
    }
    await player.setVolume(volume);
    await player.seek(Duration.zero);
    unawaited(player.play());
  }

  Future<void> playSequence(List<String> notes, double volume) async {
    for (final note in notes) {
      await play(note, volume);
      await Future<void>.delayed(const Duration(milliseconds: 430));
    }
  }

  Future<void> dispose() async {
    for (final player in _players.values) {
      await player.dispose();
    }
  }
}

class PianoScreen extends StatefulWidget {
  const PianoScreen({super.key, required this.tr, required this.showLabels, required this.vibration});
  final String Function(String) tr;
  final bool showLabels;
  final bool vibration;

  @override
  State<PianoScreen> createState() => _PianoScreenState();
}

class _PianoScreenState extends State<PianoScreen> {
  final NotePlayer player = NotePlayer();
  double volume = 0.8;
  int bpm = 90;
  Timer? metronome;
  String? pressed;

  static const whiteNotes = <String>['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5', 'D5', 'E5', 'F5', 'G5', 'A5', 'B5'];
  static const blackKeys = <(int, String)>[(0, 'Cs4'), (1, 'Ds4'), (3, 'Fs4'), (4, 'Gs4'), (5, 'As4'), (7, 'Cs5'), (8, 'Ds5'), (10, 'Fs5'), (11, 'Gs5'), (12, 'As5')];

  void play(String note) {
    setState(() => pressed = note);
    if (widget.vibration) HapticFeedback.selectionClick();
    unawaited(player.play(note, volume));
    Future<void>.delayed(const Duration(milliseconds: 130), () {
      if (mounted && pressed == note) setState(() => pressed = null);
    });
  }

  void toggleMetronome() {
    if (metronome != null) {
      metronome!.cancel();
      setState(() => metronome = null);
      return;
    }
    setState(() {
      metronome = Timer.periodic(
        Duration(milliseconds: (60000 / bpm).round()),
        (_) => HapticFeedback.lightImpact(),
      );
    });
  }

  @override
  void dispose() {
    metronome?.cancel();
    unawaited(player.dispose());
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    const keyWidth = 58.0;
    return Scaffold(
      appBar: AppBar(title: Text(widget.tr('piano'))),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
            child: Row(
              children: [
                Text('${widget.tr('volume')}: ${(volume * 100).round()}%'),
                Expanded(
                  child: Slider(value: volume, onChanged: (value) => setState(() => volume = value)),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: [
                IconButton.filledTonal(
                  onPressed: toggleMetronome,
                  icon: Icon(metronome == null ? Icons.timer_outlined : Icons.stop_rounded),
                ),
                const SizedBox(width: 10),
                Text('${widget.tr('bpm')}: $bpm'),
                Expanded(
                  child: Slider(
                    min: 40,
                    max: 200,
                    divisions: 160,
                    value: bpm.toDouble(),
                    onChanged: (value) {
                      metronome?.cancel();
                      setState(() {
                        bpm = value.round();
                        metronome = null;
                      });
                    },
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          Expanded(
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: SizedBox(
                width: keyWidth * whiteNotes.length,
                child: Stack(
                  children: [
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: whiteNotes.map((note) {
                        final active = pressed == note;
                        return GestureDetector(
                          behavior: HitTestBehavior.opaque,
                          onTapDown: (_) => play(note),
                          child: AnimatedContainer(
                            duration: const Duration(milliseconds: 80),
                            width: keyWidth,
                            margin: const EdgeInsets.all(1),
                            decoration: BoxDecoration(
                              color: active ? Theme.of(context).colorScheme.primaryContainer : Colors.white,
                              border: Border.all(color: Colors.black54),
                              borderRadius: const BorderRadius.vertical(bottom: Radius.circular(8)),
                            ),
                            alignment: Alignment.bottomCenter,
                            padding: const EdgeInsets.only(bottom: 18),
                            child: widget.showLabels ? Text(note, style: const TextStyle(color: Colors.black87, fontWeight: FontWeight.bold)) : null,
                          ),
                        );
                      }).toList(),
                    ),
                    for (final item in blackKeys)
                      Positioned(
                        left: (item.$1 + 1) * keyWidth - 18,
                        top: 0,
                        child: GestureDetector(
                          behavior: HitTestBehavior.opaque,
                          onTapDown: (_) => play(item.$2),
                          child: AnimatedContainer(
                            duration: const Duration(milliseconds: 80),
                            width: 36,
                            height: 170,
                            decoration: BoxDecoration(
                              color: pressed == item.$2 ? Theme.of(context).colorScheme.primary : Colors.black87,
                              borderRadius: const BorderRadius.vertical(bottom: Radius.circular(7)),
                              boxShadow: const [BoxShadow(blurRadius: 4, offset: Offset(0, 2))],
                            ),
                            alignment: Alignment.bottomCenter,
                            padding: const EdgeInsets.only(bottom: 12),
                            child: widget.showLabels ? Text(item.$2.replaceFirst('s', '♯'), style: const TextStyle(color: Colors.white, fontSize: 11)) : null,
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class ViolinScreen extends StatefulWidget {
  const ViolinScreen({super.key, required this.tr, required this.showLabels, required this.vibration});
  final String Function(String) tr;
  final bool showLabels;
  final bool vibration;

  @override
  State<ViolinScreen> createState() => _ViolinScreenState();
}

class _ViolinScreenState extends State<ViolinScreen> {
  final NotePlayer player = NotePlayer();
  double volume = 0.8;
  String bow = '↓';
  String? active;

  static const strings = <String, List<String>>{
    'G': ['G3', 'A3', 'B3', 'C4'],
    'D': ['D4', 'E4', 'F4', 'G4'],
    'A': ['A4', 'B4', 'C5', 'D5'],
    'E': ['E5', 'F5', 'G5', 'A5'],
  };

  void play(String note) {
    setState(() {
      active = note;
      bow = bow == '↓' ? '↑' : '↓';
    });
    if (widget.vibration) HapticFeedback.selectionClick();
    unawaited(player.play(note, volume));
  }

  @override
  void dispose() {
    unawaited(player.dispose());
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.tr('violin'))),
      body: ListView(
        padding: const EdgeInsets.all(18),
        children: [
          Row(
            children: [
              Text('${widget.tr('volume')}: ${(volume * 100).round()}%'),
              Expanded(child: Slider(value: volume, onChanged: (value) => setState(() => volume = value))),
            ],
          ),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.swap_vert_rounded),
                  const SizedBox(width: 8),
                  Text('Bow $bow', style: Theme.of(context).textTheme.headlineSmall),
                ],
              ),
            ),
          ),
          const SizedBox(height: 18),
          Container(
            padding: const EdgeInsets.symmetric(vertical: 22, horizontal: 12),
            decoration: BoxDecoration(
              color: const Color(0xff3d2418),
              borderRadius: BorderRadius.circular(22),
            ),
            child: Column(
              children: strings.entries.map((entry) {
                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 9),
                  child: Row(
                    children: [
                      SizedBox(width: 32, child: Text(entry.key, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18))),
                      Expanded(
                        child: Row(
                          children: entry.value.asMap().entries.map((position) {
                            final note = position.value;
                            final selected = note == active;
                            return Expanded(
                              child: Semantics(
                                button: true,
                                label: 'String ${entry.key}, finger ${position.key}, note $note',
                                child: InkWell(
                                  onTap: () => play(note),
                                  borderRadius: BorderRadius.circular(30),
                                  child: AnimatedContainer(
                                    duration: const Duration(milliseconds: 100),
                                    height: 54,
                                    margin: const EdgeInsets.symmetric(horizontal: 3),
                                    decoration: BoxDecoration(
                                      shape: BoxShape.circle,
                                      color: selected ? Theme.of(context).colorScheme.primary : Colors.white,
                                      border: Border.all(color: Colors.amber.shade200, width: 2),
                                    ),
                                    alignment: Alignment.center,
                                    child: Text(
                                      widget.showLabels ? note : '${position.key}',
                                      style: TextStyle(color: selected ? Colors.white : Colors.black87, fontWeight: FontWeight.bold),
                                    ),
                                  ),
                                ),
                              ),
                            );
                          }).toList(),
                        ),
                      ),
                    ],
                  ),
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }
}

class LessonsScreen extends StatelessWidget {
  const LessonsScreen({super.key, required this.tr, required this.showLabels, required this.vibration, required this.onComplete});
  final String Function(String) tr;
  final bool showLabels;
  final bool vibration;
  final Future<void> Function() onComplete;

  static const lessons = <({String title, String description, List<String> notes, IconData icon})>[
    (title: 'Piano 1: Middle C', description: 'Find Middle C and play C-D-E-D-C slowly.', notes: ['C4', 'D4', 'E4', 'D4', 'C4'], icon: Icons.piano),
    (title: 'Piano 2: Basic rhythm', description: 'Play four equal quarter notes with steady timing.', notes: ['C4', 'C4', 'C4', 'C4'], icon: Icons.timer),
    (title: 'Piano 3: C major scale', description: 'Play the white keys from C to C.', notes: ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5'], icon: Icons.stairs),
    (title: 'Violin 1: Open strings', description: 'Listen to G, D, A and E and remember their order.', notes: ['G3', 'D4', 'A4', 'E5'], icon: Icons.music_note),
    (title: 'Violin 2: First position', description: 'Place fingers 1, 2 and 3 carefully on the D string.', notes: ['D4', 'E4', 'F4', 'G4'], icon: Icons.pan_tool_alt),
    (title: 'Violin 3: String crossing', description: 'Move smoothly between D and A strings.', notes: ['D4', 'A4', 'D4', 'A4'], icon: Icons.swap_vert),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(tr('lessons'))),
      body: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: lessons.length,
        separatorBuilder: (_, __) => const SizedBox(height: 10),
        itemBuilder: (context, index) {
          final lesson = lessons[index];
          return Card(
            child: ListTile(
              minVerticalPadding: 16,
              leading: CircleAvatar(child: Icon(lesson.icon)),
              title: Text(lesson.title),
              subtitle: Text(lesson.description, maxLines: 2, overflow: TextOverflow.ellipsis),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (_) => LessonDetailScreen(
                    tr: tr,
                    title: lesson.title,
                    description: lesson.description,
                    notes: lesson.notes,
                    onComplete: onComplete,
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

class LessonDetailScreen extends StatefulWidget {
  const LessonDetailScreen({super.key, required this.tr, required this.title, required this.description, required this.notes, required this.onComplete});
  final String Function(String) tr;
  final String title;
  final String description;
  final List<String> notes;
  final Future<void> Function() onComplete;

  @override
  State<LessonDetailScreen> createState() => _LessonDetailScreenState();
}

class _LessonDetailScreenState extends State<LessonDetailScreen> {
  final NotePlayer player = NotePlayer();
  bool completed = false;

  @override
  void dispose() {
    unawaited(player.dispose());
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.title)),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Icon(Icons.school_rounded, size: 72, color: Theme.of(context).colorScheme.primary),
          const SizedBox(height: 18),
          Text(widget.description, style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 24),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: widget.notes.map((note) => Chip(label: Text(note), avatar: const Icon(Icons.music_note, size: 18))).toList(),
          ),
          const SizedBox(height: 28),
          FilledButton.icon(
            onPressed: () => player.playSequence(widget.notes, 0.8),
            icon: const Icon(Icons.play_arrow_rounded),
            label: Text(widget.tr('demo')),
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: completed
                ? null
                : () async {
                    await widget.onComplete();
                    if (mounted) setState(() => completed = true);
                  },
            icon: Icon(completed ? Icons.check_circle : Icons.task_alt),
            label: Text(completed ? '✓ ${widget.tr('complete')}' : widget.tr('complete')),
          ),
        ],
      ),
    );
  }
}

class PracticeScreen extends StatefulWidget {
  const PracticeScreen({super.key, required this.tr, required this.vibration, required this.onSaveScore});
  final String Function(String) tr;
  final bool vibration;
  final Future<void> Function(int) onSaveScore;

  @override
  State<PracticeScreen> createState() => _PracticeScreenState();
}

class _PracticeScreenState extends State<PracticeScreen> {
  final NotePlayer player = NotePlayer();
  final expected = <String>['C4', 'D4', 'E4', 'F4', 'G4'];
  int index = 0;
  int correct = 0;
  int attempts = 0;

  int get score => attempts == 0 ? 0 : ((correct / attempts) * 100).round();

  void tap(String note) {
    unawaited(player.play(note, 0.8));
    if (widget.vibration) HapticFeedback.selectionClick();
    setState(() {
      attempts += 1;
      if (note == expected[index]) {
        correct += 1;
        index = (index + 1) % expected.length;
      }
    });
    unawaited(widget.onSaveScore(score));
  }

  @override
  void dispose() {
    unawaited(player.dispose());
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    const choices = <String>['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4'];
    return Scaffold(
      appBar: AppBar(title: Text(widget.tr('practice'))),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    Column(children: [Text(widget.tr('next')), Text(expected[index], style: Theme.of(context).textTheme.headlineMedium)]),
                    Column(children: [Text(widget.tr('accuracy')), Text('$score%', style: Theme.of(context).textTheme.headlineMedium)]),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 22),
            Wrap(
              spacing: 10,
              runSpacing: 10,
              alignment: WrapAlignment.center,
              children: choices.map((note) {
                return SizedBox(
                  width: 82,
                  height: 62,
                  child: FilledButton.tonal(onPressed: () => tap(note), child: Text(note)),
                );
              }).toList(),
            ),
            const Spacer(),
            LinearProgressIndicator(value: index / expected.length),
            const SizedBox(height: 10),
            Text(expected.join('  •  ')),
          ],
        ),
      ),
    );
  }
}

class ProgressScreen extends StatelessWidget {
  const ProgressScreen({super.key, required this.tr, required this.completed, required this.best, required this.streak});
  final String Function(String) tr;
  final int completed;
  final int best;
  final int streak;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(tr('progress'))),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          _ProgressTile(icon: Icons.check_circle_rounded, label: tr('completed'), value: '$completed'),
          _ProgressTile(icon: Icons.emoji_events_rounded, label: tr('best'), value: '$best%'),
          _ProgressTile(icon: Icons.local_fire_department_rounded, label: tr('streak'), value: '$streak ${tr('days')}'),
          const SizedBox(height: 20),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Achievements', style: Theme.of(context).textTheme.titleLarge),
                  const SizedBox(height: 12),
                  _Achievement(label: 'First Lesson', unlocked: completed >= 1),
                  _Achievement(label: 'Five Lessons', unlocked: completed >= 5),
                  _Achievement(label: 'Perfect Exercise', unlocked: best == 100),
                  _Achievement(label: 'Seven-Day Streak', unlocked: streak >= 7),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ProgressTile extends StatelessWidget {
  const _ProgressTile({required this.icon, required this.label, required this.value});
  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(leading: Icon(icon), title: Text(label), trailing: Text(value, style: Theme.of(context).textTheme.titleLarge)),
    );
  }
}

class _Achievement extends StatelessWidget {
  const _Achievement({required this.label, required this.unlocked});
  final String label;
  final bool unlocked;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: Icon(unlocked ? Icons.workspace_premium_rounded : Icons.lock_outline_rounded),
      title: Text(label),
      subtitle: Text(unlocked ? 'Unlocked' : 'Keep practicing'),
    );
  }
}

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({
    super.key,
    required this.tr,
    required this.language,
    required this.themeMode,
    required this.showLabels,
    required this.vibration,
    required this.onChanged,
    required this.onReset,
  });

  final String Function(String) tr;
  final String language;
  final ThemeMode themeMode;
  final bool showLabels;
  final bool vibration;
  final Future<void> Function({String? language, ThemeMode? themeMode, bool? showLabels, bool? vibration}) onChanged;
  final Future<void> Function() onReset;

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late String language;
  late ThemeMode themeMode;
  late bool showLabels;
  late bool vibration;

  @override
  void initState() {
    super.initState();
    language = widget.language;
    themeMode = widget.themeMode;
    showLabels = widget.showLabels;
    vibration = widget.vibration;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.tr('settings'))),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          DropdownButtonFormField<String>(
            initialValue: language,
            decoration: InputDecoration(labelText: widget.tr('language'), prefixIcon: const Icon(Icons.language_rounded)),
            items: const [DropdownMenuItem(value: 'en', child: Text('English')), DropdownMenuItem(value: 'ar', child: Text('العربية'))],
            onChanged: (value) async {
              if (value == null) return;
              setState(() => language = value);
              await widget.onChanged(language: value);
            },
          ),
          const SizedBox(height: 16),
          DropdownButtonFormField<ThemeMode>(
            initialValue: themeMode,
            decoration: InputDecoration(labelText: widget.tr('theme'), prefixIcon: const Icon(Icons.palette_outlined)),
            items: [
              DropdownMenuItem(value: ThemeMode.system, child: Text(widget.tr('system'))),
              DropdownMenuItem(value: ThemeMode.light, child: Text(widget.tr('light'))),
              DropdownMenuItem(value: ThemeMode.dark, child: Text(widget.tr('dark'))),
            ],
            onChanged: (value) async {
              if (value == null) return;
              setState(() => themeMode = value);
              await widget.onChanged(themeMode: value);
            },
          ),
          const SizedBox(height: 12),
          SwitchListTile(
            title: Text(widget.tr('labels')),
            secondary: const Icon(Icons.abc_rounded),
            value: showLabels,
            onChanged: (value) async {
              setState(() => showLabels = value);
              await widget.onChanged(showLabels: value);
            },
          ),
          SwitchListTile(
            title: Text(widget.tr('vibration')),
            secondary: const Icon(Icons.vibration_rounded),
            value: vibration,
            onChanged: (value) async {
              setState(() => vibration = value);
              await widget.onChanged(vibration: value);
            },
          ),
          const Divider(height: 30),
          ListTile(
            leading: const Icon(Icons.info_outline_rounded),
            title: Text(widget.tr('about')),
            onTap: () => showAboutDialog(
              context: context,
              applicationName: 'Piano & Violin Academy',
              applicationVersion: '1.0.0',
              applicationLegalese: 'Offline learning app. No ads. No account required. Audio is generated and royalty-free.',
            ),
          ),
          ListTile(
            leading: const Icon(Icons.delete_outline_rounded),
            title: Text(widget.tr('reset')),
            onTap: () async {
              await widget.onReset();
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(widget.tr('reset'))));
              }
            },
          ),
        ],
      ),
    );
  }
}
