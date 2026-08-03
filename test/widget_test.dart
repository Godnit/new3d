import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:piano_violin_academy/main.dart';

void main() {
  testWidgets('home screen renders core learning choices', (tester) async {
    SharedPreferences.setMockInitialValues(<String, Object>{});
    final prefs = await SharedPreferences.getInstance();
    await tester.pumpWidget(AcademyApp(prefs: prefs));
    await tester.pumpAndSettle();
    expect(find.text('Piano & Violin Academy'), findsOneWidget);
    expect(find.text('Learn Piano'), findsOneWidget);
    expect(find.text('Learn Violin'), findsOneWidget);
  });
}
