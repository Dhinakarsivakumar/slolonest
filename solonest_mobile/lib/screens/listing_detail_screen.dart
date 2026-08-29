import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../services/api_service.dart';

class ListingDetailScreen extends StatefulWidget {
  final int? listingId;

  const ListingDetailScreen({super.key, this.listingId});

  @override
  State<ListingDetailScreen> createState() => _ListingDetailScreenState();
}

class _ListingDetailScreenState extends State<ListingDetailScreen> {
  int? _resolvedListingId;
  Future<Map<String, dynamic>>? _detailFuture;
  int _currentImageIndex = 0;
  bool _isBookingLoading = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_resolvedListingId == null) {
      final args = ModalRoute.of(context)?.settings.arguments;
      if (widget.listingId != null) {
        _resolvedListingId = widget.listingId;
      } else if (args is int) {
        _resolvedListingId = args;
      } else if (args is String) {
        _resolvedListingId = int.tryParse(args);
      } else if (args is Map && args['id'] != null) {
        _resolvedListingId = args['id'] is int
            ? args['id']
            : int.tryParse(args['id'].toString());
      }

      if (_resolvedListingId != null) {
        _loadDetail();
      }
    }
  }

  void _loadDetail() {
    if (_resolvedListingId != null) {
      setState(() {
        _detailFuture = ApiService.fetchListingDetail(_resolvedListingId!);
      });
    }
  }

  List<String> _extractImages(Map<String, dynamic> data) {
    final List<String> images = [];

    // Extract from images array
    if (data['images'] is List) {
      for (final img in (data['images'] as List)) {
        if (img is String && img.isNotEmpty) {
          images.add(ApiService.getImageUrl(img));
        } else if (img is Map && img['image'] != null && img['image'].toString().isNotEmpty) {
          images.add(ApiService.getImageUrl(img['image'].toString()));
        }
      }
    }

    // Extract single image fields if not already added
    final singleImageFields = ['image', 'main_image', 'cover_image'];
    for (final field in singleImageFields) {
      if (data[field] != null && data[field].toString().isNotEmpty) {
        final url = ApiService.getImageUrl(data[field].toString());
        if (!images.contains(url)) {
          images.add(url);
        }
      }
    }

    return images;
  }

  String _formatRoomType(dynamic roomType) {
    if (roomType == null) return 'Room';
    final str = roomType.toString().toLowerCase();
    if (str.contains('hotel')) return 'Hotel';
    if (str.contains('pg_private')) return 'PG - Private Room';
    if (str.contains('pg_shared') || str.contains('pg')) return 'PG / Shared Room';
    if (str.contains('homestay_private')) return 'Homestay - Private';
    if (str.contains('homestay')) return 'Homestay';
    if (str.contains('rental') || str.contains('full_house')) return 'Rental House';
    if (str.contains('private')) return 'Private Room';
    if (str.contains('shared')) return 'Shared Room';
    return roomType.toString();
  }

  Widget _buildAmenityItem(IconData icon, String title, bool isAvailable) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: isAvailable ? const Color(0xFFF0FDF4) : const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isAvailable ? const Color(0xFFBBF7D0) : const Color(0xFFE2E8F0),
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            size: 20,
            color: isAvailable ? const Color(0xFF16A34A) : const Color(0xFF94A3B8),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: isAvailable ? const Color(0xFF14532D) : const Color(0xFF64748B),
                  ),
                ),
                Text(
                  isAvailable ? 'Available' : 'Not Available',
                  style: TextStyle(
                    fontSize: 11,
                    color: isAvailable ? const Color(0xFF16A34A) : const Color(0xFF94A3B8),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _handleBookNow(BuildContext context, Map<String, dynamic> listing) async {
    final now = DateTime.now();
    final initialDateRange = DateTimeRange(
      start: now.add(const Duration(days: 1)),
      end: now.add(const Duration(days: 3)),
    );

    final DateTimeRange? pickedRange = await showDateRangePicker(
      context: context,
      firstDate: now,
      lastDate: now.add(const Duration(days: 365)),
      initialDateRange: initialDateRange,
      helpText: 'Select Check-in & Check-out Dates',
      cancelText: 'Cancel',
      confirmText: 'Select Dates',
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: const ColorScheme.light(
              primary: Color(0xFF4F46E5),
              onPrimary: Colors.white,
              surface: Colors.white,
              onSurface: Color(0xFF0F1B2D),
            ),
          ),
          child: child!,
        );
      },
    );

    if (pickedRange == null) return;

    final checkInStr =
        "${pickedRange.start.year.toString().padLeft(4, '0')}-${pickedRange.start.month.toString().padLeft(2, '0')}-${pickedRange.start.day.toString().padLeft(2, '0')}";
    final checkOutStr =
        "${pickedRange.end.year.toString().padLeft(4, '0')}-${pickedRange.end.month.toString().padLeft(2, '0')}-${pickedRange.end.day.toString().padLeft(2, '0')}";
    final daysCount = pickedRange.end.difference(pickedRange.start).inDays;

    if (!mounted) return;

    // Show Confirmation Dialog
    final bool? confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Row(
          children: [
            Icon(Icons.calendar_month_rounded, color: Color(0xFF4F46E5)),
            SizedBox(width: 8),
            Text('Confirm Booking', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              listing['title']?.toString() ?? 'Room Booking',
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFFF8FAFC),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: const Color(0xFFE2E8F0)),
              ),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Check-In:', style: TextStyle(color: Color(0xFF64748B), fontSize: 13)),
                      Text(checkInStr, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Check-Out:', style: TextStyle(color: Color(0xFF64748B), fontSize: 13)),
                      Text(checkOutStr, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Duration:', style: TextStyle(color: Color(0xFF64748B), fontSize: 13)),
                      Text('$daysCount day(s)', style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: const Color(0xFFF0FDF4),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Row(
                children: [
                  Icon(Icons.verified_user, color: Color(0xFF16A34A), size: 18),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Pay at property during check-in. No advance fee!',
                      style: TextStyle(
                        color: Color(0xFF15803D),
                        fontWeight: FontWeight.w500,
                        fontSize: 12,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel', style: TextStyle(color: Color(0xFF64748B))),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF4F46E5),
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            ),
            child: const Text('Confirm Request'),
          ),
        ],
      ),
    );

    if (confirmed != true || !mounted) return;

    setState(() {
      _isBookingLoading = true;
    });

    final id = _resolvedListingId ?? (listing['id'] is int ? listing['id'] : int.tryParse(listing['id'].toString()) ?? 0);
    final result = await ApiService.createBooking(id, checkInStr, checkOutStr);

    if (!mounted) return;

    setState(() {
      _isBookingLoading = false;
    });

    if (result['success'] == true || result['id'] != null || result['status'] != null) {
      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: const BoxDecoration(
                  color: Color(0xFFDCFCE7),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.check_circle_rounded, color: Color(0xFF16A34A), size: 54),
              ),
              const SizedBox(height: 16),
              const Text(
                'Booking Request Sent!',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF0F1B2D)),
              ),
              const SizedBox(height: 8),
              const Text(
                'Your request has been submitted to the host. You can pay at the property upon check-in.',
                textAlign: TextAlign.center,
                style: TextStyle(color: Color(0xFF64748B), fontSize: 13),
              ),
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () => Navigator.pop(ctx),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF4F46E5),
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  child: const Text('OK'),
                ),
              ),
            ],
          ),
        ),
      );
    } else {
      final errorMsg = result['error'] ?? result['message'] ?? 'Could not create booking. Please try again.';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(errorMsg.toString()),
          backgroundColor: Colors.redAccent,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_resolvedListingId == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Listing Detail')),
        body: const Center(child: Text('Invalid listing ID')),
      );
    }

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _detailFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Scaffold(
              body: Center(
                child: CircularProgressIndicator(color: Color(0xFF4F46E5)),
              ),
            );
          }

          if (snapshot.hasError || !snapshot.hasData || snapshot.data!.isEmpty) {
            return Scaffold(
              appBar: AppBar(
                title: const Text('Room Details'),
                backgroundColor: const Color(0xFF0F1B2D),
              ),
              body: Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline, size: 54, color: Color(0xFF94A3B8)),
                      const SizedBox(height: 12),
                      const Text(
                        'Unable to load listing details',
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _loadDetail,
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                ),
              ),
            );
          }

          final listing = snapshot.data!;
          final images = _extractImages(listing);

          final title = listing['title']?.toString() ?? 'Room Listing';
          final city = listing['city']?.toString() ?? '';
          final area = listing['area']?.toString() ?? '';
          final address = listing['address']?.toString() ?? '';
          final description = listing['description']?.toString() ?? 'No description provided.';
          final roomType = _formatRoomType(listing['room_type']);
          final isVerified = listing['is_verified'] == true || listing['verified'] == true;

          final priceDay = listing['price_per_day'];
          final priceMonth = listing['price_per_month'];

          final hasWifi = listing['wifi'] == true;
          final hasAc = listing['ac'] == true;
          final hasBathroom = listing['attached_bathroom'] == true;
          final hasFood = listing['food_included'] == true || listing['food'] == true;
          final hasParking = listing['parking'] == true;

          // Owner info
          String ownerName = 'SoloNest Verified Host';
          if (listing['owner'] is Map) {
            final ownerMap = listing['owner'] as Map;
            ownerName = ownerMap['name'] ?? ownerMap['full_name'] ?? ownerMap['username'] ?? ownerName;
          } else if (listing['owner_name'] != null) {
            ownerName = listing['owner_name'].toString();
          }

          return Stack(
            children: [
              CustomScrollView(
                slivers: [
                  // App Bar with Image Carousel
                  SliverAppBar(
                    expandedHeight: 280,
                    pinned: true,
                    backgroundColor: const Color(0xFF0F1B2D),
                    leading: Container(
                      margin: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: Colors.black.withOpacity(0.4),
                        shape: BoxShape.circle,
                      ),
                      child: IconButton(
                        icon: const Icon(Icons.arrow_back, color: Colors.white, size: 20),
                        onPressed: () => Navigator.pop(context),
                      ),
                    ),
                    flexibleSpace: FlexibleSpaceBar(
                      background: images.isNotEmpty
                          ? Stack(
                              children: [
                                PageView.builder(
                                  itemCount: images.length,
                                  onPageChanged: (index) {
                                    setState(() {
                                      _currentImageIndex = index;
                                    });
                                  },
                                  itemBuilder: (context, index) {
                                    return CachedNetworkImage(
                                      imageUrl: images[index],
                                      fit: BoxFit.cover,
                                      width: double.infinity,
                                      placeholder: (context, url) => Container(
                                        color: const Color(0xFFE2E8F0),
                                        child: const Center(
                                          child: CircularProgressIndicator(
                                            strokeWidth: 2,
                                            color: Color(0xFF4F46E5),
                                          ),
                                        ),
                                      ),
                                      errorWidget: (context, url, error) => Container(
                                        color: const Color(0xFFE2E8F0),
                                        child: const Center(
                                          child: Icon(Icons.image_not_supported, size: 48, color: Color(0xFF94A3B8)),
                                        ),
                                      ),
                                    );
                                  },
                                ),
                                // Counter Badge
                                Positioned(
                                  bottom: 16,
                                  right: 16,
                                  child: Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                    decoration: BoxDecoration(
                                      color: Colors.black.withOpacity(0.65),
                                      borderRadius: BorderRadius.circular(16),
                                    ),
                                    child: Text(
                                      '${_currentImageIndex + 1} / ${images.length}',
                                      style: const TextStyle(
                                        color: Colors.white,
                                        fontSize: 12,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ),
                                ),
                              ],
                            )
                          : Container(
                              color: const Color(0xFFE2E8F0),
                              child: const Center(
                                child: Icon(Icons.home_work_outlined, size: 64, color: Color(0xFF94A3B8)),
                              ),
                            ),
                    ),
                  ),

                  // Detail Body
                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // Type & Verified Row
                          Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                decoration: BoxDecoration(
                                  color: const Color(0xFFEEF2FF),
                                  borderRadius: BorderRadius.circular(6),
                                ),
                                child: Text(
                                  roomType,
                                  style: const TextStyle(
                                    color: Color(0xFF4F46E5),
                                    fontWeight: FontWeight.bold,
                                    fontSize: 12,
                                  ),
                                ),
                              ),
                              const SizedBox(width: 8),
                              if (isVerified)
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: const Color(0xFFF0FDF4),
                                    borderRadius: BorderRadius.circular(6),
                                    border: Border.all(color: const Color(0xFFBBF7D0)),
                                  ),
                                  child: const Row(
                                    children: [
                                      Icon(Icons.verified, size: 14, color: Color(0xFF16A34A)),
                                      SizedBox(width: 4),
                                      Text(
                                        'Verified Property',
                                        style: TextStyle(
                                          color: Color(0xFF15803D),
                                          fontWeight: FontWeight.bold,
                                          fontSize: 11,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                            ],
                          ),
                          const SizedBox(height: 10),

                          // Title
                          Text(
                            title,
                            style: const TextStyle(
                              fontSize: 22,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFF0F1B2D),
                            ),
                          ),
                          const SizedBox(height: 8),

                          // Location info
                          Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Icon(Icons.location_on, size: 18, color: Color(0xFF4F46E5)),
                              const SizedBox(width: 4),
                              Expanded(
                                child: Text(
                                  address.isNotEmpty ? '$address, ${area.isNotEmpty ? '$area, ' : ''}$city' : (area.isNotEmpty ? '$area, $city' : city),
                                  style: const TextStyle(
                                    color: Color(0xFF475569),
                                    fontSize: 14,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 16),

                          // Price Card
                          Container(
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(
                              color: const Color(0xFFEEF2FF),
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(color: const Color(0xFFC7D2FE)),
                            ),
                            child: Row(
                              children: [
                                if (priceDay != null && priceDay.toString() != '0')
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        const Text('Daily Rate', style: TextStyle(color: Color(0xFF64748B), fontSize: 12)),
                                        const SizedBox(height: 2),
                                        Text(
                                          '₹$priceDay',
                                          style: const TextStyle(
                                            color: Color(0xFF4F46E5),
                                            fontWeight: FontWeight.bold,
                                            fontSize: 20,
                                          ),
                                        ),
                                        const Text('/ day', style: TextStyle(color: Color(0xFF64748B), fontSize: 11)),
                                      ],
                                    ),
                                  ),
                                if (priceDay != null && priceDay.toString() != '0' && priceMonth != null && priceMonth.toString() != '0')
                                  Container(width: 1, height: 40, color: const Color(0xFFCBD5E1)),
                                if (priceMonth != null && priceMonth.toString() != '0')
                                  Expanded(
                                    child: Padding(
                                      padding: EdgeInsets.only(left: (priceDay != null && priceDay.toString() != '0') ? 16 : 0),
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          const Text('Monthly Rate', style: TextStyle(color: Color(0xFF64748B), fontSize: 12)),
                                          const SizedBox(height: 2),
                                          Text(
                                            '₹$priceMonth',
                                            style: const TextStyle(
                                              color: Color(0xFF0F1B2D),
                                              fontWeight: FontWeight.bold,
                                              fontSize: 20,
                                            ),
                                          ),
                                          const Text('/ month', style: TextStyle(color: Color(0xFF64748B), fontSize: 11)),
                                        ],
                                      ),
                                    ),
                                  ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 16),

                          // 'Pay at Property' Guarantee Badge
                          Container(
                            padding: const EdgeInsets.all(14),
                            decoration: BoxDecoration(
                              color: const Color(0xFFF0FDF4),
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: const Color(0xFFBBF7D0)),
                            ),
                            child: const Row(
                              children: [
                                Icon(
                                  Icons.verified_user_rounded,
                                  color: Color(0xFF16A34A),
                                  size: 28,
                                ),
                                SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        '100% Pay at Property Guarantee',
                                        style: TextStyle(
                                          color: Color(0xFF15803D),
                                          fontWeight: FontWeight.bold,
                                          fontSize: 14,
                                        ),
                                      ),
                                      SizedBox(height: 2),
                                      Text(
                                        'No advance deposit or online fee required. Inspect the room and pay directly upon check-in.',
                                        style: TextStyle(
                                          color: Color(0xFF166534),
                                          fontSize: 12,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 24),

                          // Amenities Grid
                          const Text(
                            'Amenities',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFF0F1B2D),
                            ),
                          ),
                          const SizedBox(height: 12),
                          GridView.count(
                            crossAxisCount: 2,
                            crossAxisSpacing: 10,
                            mainAxisSpacing: 10,
                            shrinkWrap: true,
                            physics: const NeverScrollableScrollPhysics(),
                            childAspectRatio: 2.6,
                            children: [
                              _buildAmenityItem(Icons.wifi, 'High-Speed WiFi', hasWifi),
                              _buildAmenityItem(Icons.ac_unit, 'Air Conditioning', hasAc),
                              _buildAmenityItem(Icons.bathtub_outlined, 'Attached Bath', hasBathroom),
                              _buildAmenityItem(Icons.restaurant, 'Food / Meals', hasFood),
                              _buildAmenityItem(Icons.local_parking, 'Parking Space', hasParking),
                            ],
                          ),
                          const SizedBox(height: 24),

                          // Description Text
                          const Text(
                            'About this stay',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFF0F1B2D),
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            description,
                            style: const TextStyle(
                              fontSize: 14,
                              height: 1.6,
                              color: Color(0xFF334155),
                            ),
                          ),
                          const SizedBox(height: 24),

                          // Owner Info Card
                          const Text(
                            'Host Information',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFF0F1B2D),
                            ),
                          ),
                          const SizedBox(height: 12),
                          Container(
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(color: const Color(0xFFE2E8F0)),
                              boxShadow: [
                                BoxShadow(
                                  color: Colors.black.withOpacity(0.04),
                                  blurRadius: 6,
                                  offset: const Offset(0, 2),
                                ),
                              ],
                            ),
                            child: Row(
                              children: [
                                CircleAvatar(
                                  radius: 26,
                                  backgroundColor: const Color(0xFF4F46E5),
                                  child: Text(
                                    ownerName.isNotEmpty ? ownerName[0].toUpperCase() : 'H',
                                    style: const TextStyle(
                                      color: Colors.white,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 20,
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 14),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        ownerName,
                                        style: const TextStyle(
                                          fontWeight: FontWeight.bold,
                                          fontSize: 16,
                                          color: Color(0xFF0F1B2D),
                                        ),
                                      ),
                                      const SizedBox(height: 2),
                                      const Row(
                                        children: [
                                          Icon(Icons.shield_outlined, size: 14, color: Color(0xFF10B981)),
                                          SizedBox(width: 4),
                                          Text(
                                            'SoloNest Verified Host',
                                            style: TextStyle(
                                              color: Color(0xFF10B981),
                                              fontWeight: FontWeight.w600,
                                              fontSize: 12,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ),

                          // Bottom space for fixed bar
                          const SizedBox(height: 100),
                        ],
                      ),
                    ),
                  ),
                ],
              ),

              // Fixed Bottom 'Book Now' Bar
              Positioned(
                bottom: 0,
                left: 0,
                right: 0,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.08),
                        blurRadius: 10,
                        offset: const Offset(0, -3),
                      ),
                    ],
                  ),
                  child: SafeArea(
                    top: false,
                    child: Row(
                      children: [
                        Expanded(
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                priceDay != null && priceDay.toString() != '0'
                                    ? '₹$priceDay / day'
                                    : (priceMonth != null ? '₹$priceMonth / mo' : 'Pay at Property'),
                                style: const TextStyle(
                                  fontWeight: FontWeight.bold,
                                  fontSize: 17,
                                  color: Color(0xFF0F1B2D),
                                ),
                              ),
                              const Text(
                                'No advance payment',
                                style: TextStyle(
                                  fontSize: 12,
                                  color: Color(0xFF16A34A),
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 12),
                        ElevatedButton(
                          onPressed: _isBookingLoading ? null : () => _handleBookNow(context, listing),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF4F46E5),
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 14),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                          ),
                          child: _isBookingLoading
                              ? const SizedBox(
                                  height: 20,
                                  width: 20,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: Colors.white,
                                  ),
                                )
                              : const Text(
                                  'Book Now',
                                  style: TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}
