import 'package:flutter_test/flutter_test.dart';
import 'package:voxforge_noctilith_studio/main.dart';

void main() {
  testWidgets('VoxForge shell opens dashboard', (WidgetTester tester) async {
    await tester.pumpWidget(const VoxForgeApp());
    expect(find.text('VoxForge / Noctilith'), findsOneWidget);
    expect(find.text('Prototype control deck'), findsOneWidget);
  });
}
