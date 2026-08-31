import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:connectivity_plus/connectivity_plus.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Color(0xFF0F1B2D),
    statusBarIconBrightness: Brightness.light,
  ));
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
        primaryColor: const Color(0xFF4F46E5),
        scaffoldBackgroundColor: const Color(0xFF0F1B2D),
      ),
      home: const SoloNestWebView(),
    );
  }
}

class SoloNestWebView extends StatefulWidget {
  const SoloNestWebView({Key? key}) : super(key: key);

  @override
  State<SoloNestWebView> createState() => _SoloNestWebViewState();
}

class _SoloNestWebViewState extends State<SoloNestWebView> {
  late final WebViewController _controller;
  bool _isLoading = true;
  bool _hasError = false;
  double _loadingProgress = 0;

  static const String _siteUrl = 'https://slolonest.onrender.com';

  @override
  void initState() {
    super.initState();
    _initWebView();
  }

  void _initWebView() {
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setBackgroundColor(const Color(0xFF0F1B2D))
      ..setNavigationDelegate(
        NavigationDelegate(
          onProgress: (int progress) {
            setState(() {
              _loadingProgress = progress / 100.0;
            });
          },
          onPageStarted: (String url) {
            setState(() {
              _isLoading = true;
              _hasError = false;
            });
          },
          onPageFinished: (String url) {
            setState(() {
              _isLoading = false;
            });
          },
          onWebResourceError: (WebResourceError error) {
            if (error.isForMainFrame == true) {
              setState(() {
                _hasError = true;
                _isLoading = false;
              });
            }
          },
          onNavigationRequest: (NavigationRequest request) {
            // Allow all navigation within the site
            if (request.url.startsWith(_siteUrl) ||
                request.url.startsWith('https://accounts.google.com') ||
                request.url.startsWith('https://www.google.com/maps') ||
                request.url.contains('google') ||
                request.url.startsWith('tel:') ||
                request.url.startsWith('mailto:')) {
              return NavigationDecision.navigate;
            }
            return NavigationDecision.navigate;
          },
        ),
      )
      ..enableZoom(true)
      ..loadRequest(Uri.parse(_siteUrl));
  }

  Future<bool> _onWillPop() async {
    if (await _controller.canGoBack()) {
      _controller.goBack();
      return false;
    }
    return true;
  }

  void _retryLoading() {
    setState(() {
      _hasError = false;
      _isLoading = true;
    });
    _controller.loadRequest(Uri.parse(_siteUrl));
  }

  @override
  Widget build(BuildContext context) {
    return WillPopScope(
      onWillPop: _onWillPop,
      child: Scaffold(
        backgroundColor: const Color(0xFF0F1B2D),
        body: SafeArea(
          child: Stack(
            children: [
              // WebView
              if (!_hasError)
                WebViewWidget(controller: _controller),

              // Loading indicator
              if (_isLoading && !_hasError)
                Container(
                  color: const Color(0xFF0F1B2D),
                  child: Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(
                          Icons.home_work_rounded,
                          color: Color(0xFFF59E0B),
                          size: 48,
                        ),
                        const SizedBox(height: 16),
                        const Text(
                          'SoloNest',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          'Loading...',
                          style: TextStyle(
                            color: Color(0xFF94A3B8),
                            fontSize: 14,
                          ),
                        ),
                        const SizedBox(height: 24),
                        SizedBox(
                          width: 200,
                          child: ClipRRect(
                            borderRadius: BorderRadius.circular(8),
                            child: LinearProgressIndicator(
                              value: _loadingProgress,
                              backgroundColor: const Color(0xFF1A2942),
                              valueColor: const AlwaysStoppedAnimation<Color>(
                                Color(0xFF4F46E5),
                              ),
                              minHeight: 4,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

              // Error screen
              if (_hasError)
                Container(
                  color: const Color(0xFF0F1B2D),
                  child: Center(
                    child: Padding(
                      padding: const EdgeInsets.all(32),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(
                            Icons.wifi_off_rounded,
                            color: Color(0xFF94A3B8),
                            size: 64,
                          ),
                          const SizedBox(height: 20),
                          const Text(
                            'No Internet Connection',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 8),
                          const Text(
                            'Please check your connection and try again.',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              color: Color(0xFF94A3B8),
                              fontSize: 14,
                            ),
                          ),
                          const SizedBox(height: 24),
                          ElevatedButton.icon(
                            onPressed: _retryLoading,
                            icon: const Icon(Icons.refresh),
                            label: const Text('Retry'),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: const Color(0xFF4F46E5),
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(
                                horizontal: 32,
                                vertical: 14,
                              ),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),

              // Top loading bar
              if (_isLoading && !_hasError)
                Positioned(
                  top: 0,
                  left: 0,
                  right: 0,
                  child: LinearProgressIndicator(
                    value: _loadingProgress,
                    backgroundColor: Colors.transparent,
                    valueColor: const AlwaysStoppedAnimation<Color>(
                      Color(0xFFF59E0B),
                    ),
                    minHeight: 3,
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
