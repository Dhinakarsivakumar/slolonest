import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../services/api_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final TextEditingController _searchController = TextEditingController();
  String _selectedCategory = 'all';
  late Future<List<Map<String, dynamic>>> _listingsFuture;

  final List<Map<String, String>> _categories = const [
    {'id': 'all', 'label': 'All'},
    {'id': 'hotel', 'label': 'Hotels'},
    {'id': 'pg', 'label': 'PG/Shared'},
    {'id': 'homestay', 'label': 'Homestays'},
    {'id': 'rental', 'label': 'Rentals'},
  ];

  @override
  void initState() {
    super.initState();
    _loadListings();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _loadListings() {
    setState(() {
      _listingsFuture = ApiService.fetchListings(
        city: _searchController.text.trim(),
        roomType: _selectedCategory == 'all' ? '' : _selectedCategory,
      );
    });
  }

  Future<void> _handleRefresh() async {
    _loadListings();
    await _listingsFuture;
  }

  String _getListingImageUrl(Map<String, dynamic> item) {
    if (item['image'] != null && item['image'].toString().isNotEmpty) {
      return ApiService.getImageUrl(item['image'].toString());
    }
    if (item['main_image'] != null && item['main_image'].toString().isNotEmpty) {
      return ApiService.getImageUrl(item['main_image'].toString());
    }
    if (item['cover_image'] != null && item['cover_image'].toString().isNotEmpty) {
      return ApiService.getImageUrl(item['cover_image'].toString());
    }
    if (item['images'] is List && (item['images'] as List).isNotEmpty) {
      final first = (item['images'] as List).first;
      if (first is String && first.isNotEmpty) {
        return ApiService.getImageUrl(first);
      }
      if (first is Map && first['image'] != null && first['image'].toString().isNotEmpty) {
        return ApiService.getImageUrl(first['image'].toString());
      }
    }
    return '';
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

  Widget _buildAmenityChip(IconData icon, String label) {
    return Container(
      margin: const EdgeInsets.only(right: 6, top: 4),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: const Color(0xFFF1F5F9),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: const Color(0xFF475569)),
          const SizedBox(width: 4),
          Text(
            label,
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w500,
              color: Color(0xFF475569),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0F1B2D),
        elevation: 0,
        title: const Row(
          children: [
            Icon(Icons.home_work_rounded, color: Color(0xFFF59E0B), size: 24),
            SizedBox(width: 8),
            Text(
              'SoloNest',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 20,
                color: Colors.white,
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.person_outline, color: Colors.white),
            tooltip: 'Login',
            onPressed: () {
              Navigator.pushNamed(context, '/login');
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _handleRefresh,
        color: const Color(0xFF4F46E5),
        child: CustomScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          slivers: [
            // Navy Search Header
            SliverToBoxAdapter(
              child: Container(
                color: const Color(0xFF0F1B2D),
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(12),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.08),
                            blurRadius: 8,
                            offset: const Offset(0, 2),
                          ),
                        ],
                      ),
                      child: TextField(
                        controller: _searchController,
                        textInputAction: TextInputAction.search,
                        onSubmitted: (_) => _loadListings(),
                        decoration: InputDecoration(
                          hintText: 'Search city or area (e.g. Chennai, Tanjore)...',
                          hintStyle: const TextStyle(
                            color: Color(0xFF94A3B8),
                            fontSize: 14,
                          ),
                          prefixIcon: const Icon(
                            Icons.search,
                            color: Color(0xFF4F46E5),
                            size: 20,
                          ),
                          suffixIcon: _searchController.text.isNotEmpty
                              ? IconButton(
                                  icon: const Icon(Icons.clear, size: 18, color: Color(0xFF64748B)),
                                  onPressed: () {
                                    _searchController.clear();
                                    _loadListings();
                                  },
                                )
                              : IconButton(
                                  icon: const Icon(Icons.arrow_forward, size: 18, color: Color(0xFF4F46E5)),
                                  onPressed: _loadListings,
                                ),
                          border: InputBorder.none,
                          contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // Categories Filter Row
            SliverToBoxAdapter(
              child: Container(
                color: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 12),
                child: SizedBox(
                  height: 38,
                  child: ListView.builder(
                    scrollDirection: Axis.horizontal,
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    itemCount: _categories.length,
                    itemBuilder: (context, index) {
                      final cat = _categories[index];
                      final isSelected = _selectedCategory == cat['id'];
                      return Padding(
                        padding: const EdgeInsets.only(right: 8),
                        child: ChoiceChip(
                          label: Text(cat['label']!),
                          selected: isSelected,
                          onSelected: (selected) {
                            if (selected) {
                              setState(() {
                                _selectedCategory = cat['id']!;
                              });
                              _loadListings();
                            }
                          },
                          selectedColor: const Color(0xFF4F46E5),
                          backgroundColor: const Color(0xFFF1F5F9),
                          labelStyle: TextStyle(
                            color: isSelected ? Colors.white : const Color(0xFF334155),
                            fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                            fontSize: 13,
                          ),
                          side: BorderSide(
                            color: isSelected ? const Color(0xFF4F46E5) : const Color(0xFFE2E8F0),
                          ),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(20),
                          ),
                          showCheckmark: false,
                        ),
                      );
                    },
                  ),
                ),
              ),
            ),

            // Green Trust Badge
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF0FDF4),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: const Color(0xFFBBF7D0)),
                  ),
                  child: const Row(
                    children: [
                      Icon(
                        Icons.verified_user_rounded,
                        color: Color(0xFF16A34A),
                        size: 20,
                      ),
                      SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'Pay at Property - No Advance Payment',
                          style: TextStyle(
                            color: Color(0xFF15803D),
                            fontWeight: FontWeight.w600,
                            fontSize: 13,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),

            // Listings Content (FutureBuilder)
            FutureBuilder<List<Map<String, dynamic>>>(
              future: _listingsFuture,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const SliverFillRemaining(
                    hasScrollBody: false,
                    child: Center(
                      child: Padding(
                        padding: EdgeInsets.all(40),
                        child: CircularProgressIndicator(
                          color: Color(0xFF4F46E5),
                        ),
                      ),
                    ),
                  );
                }

                if (snapshot.hasError) {
                  return SliverFillRemaining(
                    hasScrollBody: false,
                    child: Center(
                      child: Padding(
                        padding: const EdgeInsets.all(24),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(Icons.cloud_off_rounded, size: 56, color: Color(0xFF94A3B8)),
                            const SizedBox(height: 12),
                            const Text(
                              'Unable to load listings',
                              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF334155)),
                            ),
                            const SizedBox(height: 6),
                            const Text(
                              'Please check your connection and pull down to retry.',
                              textAlign: TextAlign.center,
                              style: TextStyle(color: Color(0xFF64748B), fontSize: 13),
                            ),
                            const SizedBox(height: 16),
                            ElevatedButton.icon(
                              onPressed: _loadListings,
                              icon: const Icon(Icons.refresh, size: 18),
                              label: const Text('Retry'),
                            ),
                          ],
                        ),
                      ),
                    ),
                  );
                }

                final listings = snapshot.data ?? [];

                if (listings.isEmpty) {
                  return SliverFillRemaining(
                    hasScrollBody: false,
                    child: Center(
                      child: Padding(
                        padding: const EdgeInsets.all(32),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Container(
                              padding: const EdgeInsets.all(20),
                              decoration: const BoxDecoration(
                                color: Color(0xFFEEF2FF),
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(
                                Icons.search_off_rounded,
                                size: 48,
                                color: Color(0xFF4F46E5),
                              ),
                            ),
                            const SizedBox(height: 16),
                            const Text(
                              'No listings found',
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                                color: Color(0xFF1E293B),
                              ),
                            ),
                            const SizedBox(height: 8),
                            const Text(
                              'Try adjusting your search location or category filter.',
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                fontSize: 14,
                                color: Color(0xFF64748B),
                              ),
                            ),
                            const SizedBox(height: 16),
                            if (_searchController.text.isNotEmpty || _selectedCategory != 'all')
                              OutlinedButton(
                                onPressed: () {
                                  _searchController.clear();
                                  setState(() {
                                    _selectedCategory = 'all';
                                  });
                                  _loadListings();
                                },
                                style: OutlinedButton.styleFrom(
                                  foregroundColor: const Color(0xFF4F46E5),
                                  side: const BorderSide(color: Color(0xFF4F46E5)),
                                ),
                                child: const Text('Clear Filters'),
                              ),
                          ],
                        ),
                      ),
                    ),
                  );
                }

                return SliverPadding(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  sliver: SliverList(
                    delegate: SliverChildBuilderDelegate(
                      (context, index) {
                        final item = listings[index];
                        final id = item['id'];
                        final title = item['title']?.toString() ?? 'Room Listing';
                        final city = item['city']?.toString() ?? '';
                        final area = item['area']?.toString() ?? '';
                        final roomType = _formatRoomType(item['room_type']);
                        final isVerified = item['is_verified'] == true || item['verified'] == true;
                        
                        final priceDay = item['price_per_day'];
                        final priceMonth = item['price_per_month'];
                        
                        final hasWifi = item['wifi'] == true;
                        final hasAc = item['ac'] == true;
                        final hasFood = item['food_included'] == true || item['food'] == true;
                        final hasParking = item['parking'] == true;

                        final imageUrl = _getListingImageUrl(item);

                        return Card(
                          margin: const EdgeInsets.only(bottom: 16),
                          elevation: 2,
                          shadowColor: Colors.black.withOpacity(0.08),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16),
                            side: const BorderSide(color: Color(0xFFE2E8F0)),
                          ),
                          clipBehavior: Clip.antiAlias,
                          child: InkWell(
                            onTap: () {
                              if (id != null) {
                                Navigator.pushNamed(
                                  context,
                                  '/listing',
                                  arguments: id is int ? id : int.tryParse(id.toString()),
                                );
                              }
                            },
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                // Image with Verified Badge overlay
                                Stack(
                                  children: [
                                    ClipRRect(
                                      borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
                                      child: SizedBox(
                                        height: 190,
                                        width: double.infinity,
                                        child: imageUrl.isNotEmpty
                                            ? CachedNetworkImage(
                                                imageUrl: imageUrl,
                                                fit: BoxFit.cover,
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
                                                    child: Icon(Icons.image_not_supported_outlined, size: 40, color: Color(0xFF94A3B8)),
                                                  ),
                                                ),
                                              )
                                            : Container(
                                                color: const Color(0xFFE2E8F0),
                                                child: const Center(
                                                  child: Icon(Icons.home_outlined, size: 48, color: Color(0xFF94A3B8)),
                                                ),
                                              ),
                                      ),
                                    ),
                                    if (isVerified)
                                      Positioned(
                                        top: 12,
                                        left: 12,
                                        child: Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                          decoration: BoxDecoration(
                                            color: const Color(0xFF10B981),
                                            borderRadius: BorderRadius.circular(20),
                                            boxShadow: [
                                              BoxShadow(
                                                color: Colors.black.withOpacity(0.2),
                                                blurRadius: 4,
                                                offset: const Offset(0, 2),
                                              ),
                                            ],
                                          ),
                                          child: const Row(
                                            mainAxisSize: MainAxisSize.min,
                                            children: [
                                              Icon(Icons.verified, size: 14, color: Colors.white),
                                              SizedBox(width: 4),
                                              Text(
                                                'VERIFIED',
                                                style: TextStyle(
                                                  color: Colors.white,
                                                  fontWeight: FontWeight.bold,
                                                  fontSize: 10,
                                                  letterSpacing: 0.5,
                                                ),
                                              ),
                                            ],
                                          ),
                                        ),
                                      ),
                                    Positioned(
                                      top: 12,
                                      right: 12,
                                      child: Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                        decoration: BoxDecoration(
                                          color: const Color(0xFF0F1B2D).withOpacity(0.85),
                                          borderRadius: BorderRadius.circular(20),
                                        ),
                                        child: Text(
                                          roomType,
                                          style: const TextStyle(
                                            color: Colors.white,
                                            fontWeight: FontWeight.w600,
                                            fontSize: 11,
                                          ),
                                        ),
                                      ),
                                    ),
                                  ],
                                ),

                                // Content Details
                                Padding(
                                  padding: const EdgeInsets.all(14),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      // Title
                                      Text(
                                        title,
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                        style: const TextStyle(
                                          fontSize: 16,
                                          fontWeight: FontWeight.bold,
                                          color: Color(0xFF0F1B2D),
                                        ),
                                      ),
                                      const SizedBox(height: 4),

                                      // City + Area Subtitle
                                      Row(
                                        children: [
                                          const Icon(
                                            Icons.location_on_outlined,
                                            size: 14,
                                            color: Color(0xFF64748B),
                                          ),
                                          const SizedBox(width: 4),
                                          Expanded(
                                            child: Text(
                                              area.isNotEmpty ? '$area, $city' : city,
                                              maxLines: 1,
                                              overflow: TextOverflow.ellipsis,
                                              style: const TextStyle(
                                                color: Color(0xFF64748B),
                                                fontSize: 13,
                                                fontWeight: FontWeight.w500,
                                              ),
                                            ),
                                          ),
                                        ],
                                      ),
                                      const SizedBox(height: 10),

                                      // Amenity Chips Row
                                      if (hasWifi || hasAc || hasFood || hasParking)
                                        Padding(
                                          padding: const EdgeInsets.only(bottom: 10),
                                          child: Wrap(
                                            spacing: 4,
                                            children: [
                                              if (hasWifi) _buildAmenityChip(Icons.wifi, 'WiFi'),
                                              if (hasAc) _buildAmenityChip(Icons.ac_unit, 'AC'),
                                              if (hasFood) _buildAmenityChip(Icons.restaurant, 'Food'),
                                              if (hasParking) _buildAmenityChip(Icons.local_parking, 'Parking'),
                                            ],
                                          ),
                                        ),

                                      const Divider(height: 1, color: Color(0xFFF1F5F9)),
                                      const SizedBox(height: 10),

                                      // Price Row
                                      Row(
                                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                        crossAxisAlignment: CrossAxisAlignment.center,
                                        children: [
                                          Column(
                                            crossAxisAlignment: CrossAxisAlignment.start,
                                            children: [
                                              if (priceDay != null && priceDay.toString() != '0')
                                                RichText(
                                                  text: TextSpan(
                                                    children: [
                                                      TextSpan(
                                                        text: '₹$priceDay',
                                                        style: const TextStyle(
                                                          color: Color(0xFF4F46E5),
                                                          fontWeight: FontWeight.bold,
                                                          fontSize: 16,
                                                        ),
                                                      ),
                                                      const TextSpan(
                                                        text: ' / day',
                                                        style: TextStyle(
                                                          color: Color(0xFF64748B),
                                                          fontSize: 12,
                                                        ),
                                                      ),
                                                    ],
                                                  ),
                                                ),
                                              if (priceMonth != null && priceMonth.toString() != '0')
                                                RichText(
                                                  text: TextSpan(
                                                    children: [
                                                      TextSpan(
                                                        text: '₹$priceMonth',
                                                        style: TextStyle(
                                                          color: priceDay != null && priceDay.toString() != '0'
                                                              ? const Color(0xFF0F1B2D)
                                                              : const Color(0xFF4F46E5),
                                                          fontWeight: FontWeight.bold,
                                                          fontSize: priceDay != null && priceDay.toString() != '0' ? 13 : 16,
                                                        ),
                                                      ),
                                                      TextSpan(
                                                        text: ' / month',
                                                        style: TextStyle(
                                                          color: const Color(0xFF64748B),
                                                          fontSize: priceDay != null && priceDay.toString() != '0' ? 11 : 12,
                                                        ),
                                                      ),
                                                    ],
                                                  ),
                                                ),
                                              if ((priceDay == null || priceDay.toString() == '0') &&
                                                  (priceMonth == null || priceMonth.toString() == '0'))
                                                const Text(
                                                  'Contact for price',
                                                  style: TextStyle(
                                                    color: Color(0xFF4F46E5),
                                                    fontWeight: FontWeight.bold,
                                                    fontSize: 14,
                                                  ),
                                                ),
                                            ],
                                          ),

                                          // View Details Button
                                          Container(
                                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                            decoration: BoxDecoration(
                                              color: const Color(0xFFEEF2FF),
                                              borderRadius: BorderRadius.circular(8),
                                            ),
                                            child: const Row(
                                              children: [
                                                Text(
                                                  'View Room',
                                                  style: TextStyle(
                                                    color: Color(0xFF4F46E5),
                                                    fontWeight: FontWeight.w600,
                                                    fontSize: 12,
                                                  ),
                                                ),
                                                SizedBox(width: 4),
                                                Icon(Icons.arrow_forward_ios, size: 11, color: Color(0xFF4F46E5)),
                                              ],
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
                        );
                      },
                      childCount: listings.length,
                    ),
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}
