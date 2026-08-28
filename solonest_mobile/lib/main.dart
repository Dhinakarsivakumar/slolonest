import 'package:flutter/material.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const SoloNestApp());
}

class SoloNestApp extends StatelessWidget {
  const SoloNestApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SoloNest',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF4F46E5),
          primary: const Color(0xFF4F46E5),
          secondary: const Color(0xFFF59E0B),
          surface: const Color(0xFFF8FAFC),
        ),
        scaffoldBackgroundColor: const Color(0xFFF8FAFC),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF0F1B2D),
          foregroundColor: Colors.white,
          elevation: 0,
        ),
        fontFamily: 'Inter',
      ),
      home: const HomeScreen(),
    );
  }
}
