import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = 'https://slolonest.onrender.com';

  static Future<List<dynamic>> fetchListings({String city = '', String roomType = ''}) async {
    try {
      final uri = Uri.parse('$baseUrl/api/cities/').replace(queryParameters: {
        if (city.isNotEmpty) 'city': city,
        if (roomType.isNotEmpty) 'room_type': roomType,
      });

      final response = await http.get(uri).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return data is List ? data : [];
      }
      return [];
    } catch (e) {
      return [];
    }
  }

  static String getFullImageUrl(String path) {
    if (path.startsWith('http')) return path;
    return '$baseUrl$path';
  }
}
