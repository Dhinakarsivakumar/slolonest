import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static const String baseUrl = 'https://slolonest.onrender.com';
  static const Duration timeoutDuration = Duration(seconds: 10);

  /// Helper to get common request headers
  static Future<Map<String, String>> _getHeaders() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token') ?? prefs.getString('token');
    return {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      if (token != null && token.isNotEmpty) 'Authorization': 'Bearer $token',
    };
  }

  /// Format an image URL: prepends baseUrl if path doesn't start with http/https
  static String getImageUrl(String path) {
    if (path.isEmpty) return '';
    final trimmed = path.trim();
    if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
      return trimmed;
    }
    if (trimmed.startsWith('/')) {
      return '$baseUrl$trimmed';
    }
    return '$baseUrl/$trimmed';
  }

  /// Fetch listings with optional city and roomType filters
  /// GET /api/listings/?city=X&room_type=Y
  static Future<List<Map<String, dynamic>>> fetchListings({
    String city = '',
    String roomType = '',
  }) async {
    try {
      final Map<String, String> queryParams = {};
      if (city.trim().isNotEmpty) {
        queryParams['city'] = city.trim();
      }
      if (roomType.trim().isNotEmpty && roomType.toLowerCase() != 'all') {
        queryParams['room_type'] = roomType.trim();
      }

      final uri = Uri.parse('$baseUrl/api/listings/').replace(
        queryParameters: queryParams.isNotEmpty ? queryParams : null,
      );

      final headers = await _getHeaders();
      final response = await http.get(uri, headers: headers).timeout(timeoutDuration);

      if (response.statusCode >= 200 && response.statusCode < 300) {
        final dynamic decoded = json.decode(response.body);
        if (decoded is List) {
          return decoded.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList();
        } else if (decoded is Map) {
          if (decoded['results'] is List) {
            return (decoded['results'] as List).whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList();
          } else if (decoded['listings'] is List) {
            return (decoded['listings'] as List).whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList();
          }
        }
      }
      return [];
    } catch (e) {
      debugPrint('Error fetching listings: $e');
      return [];
    }
  }

  /// Fetch single listing detail
  /// GET /api/listings/{id}/
  static Future<Map<String, dynamic>> fetchListingDetail(int id) async {
    try {
      final uri = Uri.parse('$baseUrl/api/listings/$id/');
      final headers = await _getHeaders();
      final response = await http.get(uri, headers: headers).timeout(timeoutDuration);

      if (response.statusCode >= 200 && response.statusCode < 300) {
        final dynamic decoded = json.decode(response.body);
        if (decoded is Map<String, dynamic>) {
          return decoded;
        } else if (decoded is Map) {
          return Map<String, dynamic>.from(decoded);
        }
      }
      return {};
    } catch (e) {
      debugPrint('Error fetching listing detail for id $id: $e');
      return {};
    }
  }

  /// Request phone OTP
  /// POST /api/auth/phone/ with JSON body {phone}
  static Future<Map<String, dynamic>> requestOtp(String phone) async {
    try {
      final uri = Uri.parse('$baseUrl/api/auth/phone/');
      final headers = await _getHeaders();
      final response = await http.post(
        uri,
        headers: headers,
        body: json.encode({'phone': phone.trim()}),
      ).timeout(timeoutDuration);

      if (response.statusCode >= 200 && response.statusCode < 300) {
        final dynamic decoded = json.decode(response.body);
        if (decoded is Map) {
          return Map<String, dynamic>.from(decoded);
        }
        return {'success': true};
      } else {
        try {
          final dynamic decoded = json.decode(response.body);
          if (decoded is Map) {
            return Map<String, dynamic>.from(decoded);
          }
        } catch (_) {}
        return {'success': false, 'error': 'Failed to send OTP (Status: ${response.statusCode})'};
      }
    } catch (e) {
      debugPrint('Error requesting OTP: $e');
      return {'success': false, 'error': 'Network timeout or error: $e'};
    }
  }

  /// Verify phone OTP
  /// POST /api/auth/verify/ with JSON body {phone, code}
  static Future<Map<String, dynamic>> verifyOtp(String phone, String code) async {
    try {
      final uri = Uri.parse('$baseUrl/api/auth/verify/');
      final headers = await _getHeaders();
      final response = await http.post(
        uri,
        headers: headers,
        body: json.encode({
          'phone': phone.trim(),
          'code': code.trim(),
        }),
      ).timeout(timeoutDuration);

      if (response.statusCode >= 200 && response.statusCode < 300) {
        final dynamic decoded = json.decode(response.body);
        if (decoded is Map) {
          return Map<String, dynamic>.from(decoded);
        }
        return {'success': true};
      } else {
        try {
          final dynamic decoded = json.decode(response.body);
          if (decoded is Map) {
            return Map<String, dynamic>.from(decoded);
          }
        } catch (_) {}
        return {'success': false, 'error': 'Invalid OTP or verification failed'};
      }
    } catch (e) {
      debugPrint('Error verifying OTP: $e');
      return {'success': false, 'error': 'Network timeout or error: $e'};
    }
  }

  /// Create booking
  /// POST /api/bookings/create/ with JSON body
  static Future<Map<String, dynamic>> createBooking(
    int listingId,
    String checkIn,
    String checkOut,
  ) async {
    try {
      final uri = Uri.parse('$baseUrl/api/bookings/create/');
      final headers = await _getHeaders();
      final response = await http.post(
        uri,
        headers: headers,
        body: json.encode({
          'listing_id': listingId,
          'listing': listingId,
          'check_in': checkIn,
          'check_out': checkOut,
        }),
      ).timeout(timeoutDuration);

      if (response.statusCode >= 200 && response.statusCode < 300) {
        final dynamic decoded = json.decode(response.body);
        if (decoded is Map) {
          return Map<String, dynamic>.from(decoded);
        }
        return {'success': true, 'message': 'Booking confirmed successfully!'};
      } else {
        try {
          final dynamic decoded = json.decode(response.body);
          if (decoded is Map) {
            return Map<String, dynamic>.from(decoded);
          }
        } catch (_) {}
        return {
          'success': false,
          'error': 'Failed to create booking (${response.statusCode})',
        };
      }
    } catch (e) {
      debugPrint('Error creating booking: $e');
      return {'success': false, 'error': 'Network timeout or error: $e'};
    }
  }
}
