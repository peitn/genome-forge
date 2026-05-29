import 'package:flutter_test/flutter_test.dart';
import 'package:voxforge_noctilith_studio/main.dart';

void main() {
  testWidgets('VoxForge shell opens dashboard', (WidgetTester tester) async {
    await tester.pumpWidget(const VoxForgeApp());
    await tester.pump();
    expect(find.text('VoxForge Ultimate Studio'), findsWidgets);
    expect(find.text('Dashboard'), findsOneWidget);
  });
}
