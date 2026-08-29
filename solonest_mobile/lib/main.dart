import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'screens/home_screen.dart';
import 'screens/listing_detail_screen.dart';
import 'screens/login_screen.dart';

void main() {
  runApp(const SoloNestApp());
}

class SoloNestApp extends StatelessWidget {
  const SoloNestApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SoloNest',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        scaffoldBackgroundColor: const Color(0xFFF8F9FC),
        colorScheme: ColorScheme.light(
          primary: const Color(0xFF4F46E5),
          secondary: const Color(0xFFF59E0B),
          surface: const Color(0xFFFFFFFF),
          background: const Color(0xFFF8F9FC),
          error: const Color(0xFFEF4444),
          onPrimary: const Color(0xFFFFFFFF),
          onSecondary: const Color(0xFFFFFFFF),
          onSurface: const Color(0xFF0F1B2D),
          onBackground: const Color(0xFF0F1B2D),
        ),
        textTheme: TextTheme(
          displayLarge: GoogleFonts.plusJakartaSans(
            color: const Color(0xFF0F1B2D),
            fontWeight: FontWeight.w800,
          ),
          displayMedium: GoogleFonts.plusJakartaSans(
            color: const Color(0xFF0F1B2D),
            fontWeight: FontWeight.w700,
          ),
          bodyLarge: GoogleFonts.inter(
            color: const Color(0xFF0F1B2D),
            fontWeight: FontWeight.w400,
          ),
          bodyMedium: GoogleFonts.inter(
            color: const Color(0xFF475569),
            fontWeight: FontWeight.w400,
          ),
          labelLarge: GoogleFonts.inter(
            color: const Color(0xFFFFFFFF),
            fontWeight: FontWeight.w600,
          ),
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF0F1B2D),
          foregroundColor: Colors.white,
          elevation: 0,
        ),
      ),
      initialRoute: '/',
      routes: {
        '/': (context) => const HomeScreen(),
        '/listing': (context) => const ListingDetailScreen(),
        '/login': (context) => const LoginScreen(),
      },
    );
  }
}
