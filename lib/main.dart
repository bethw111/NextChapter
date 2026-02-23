import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'NextChapter',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      home: const BookRecommendationPage(title: 'NextChapter'),
    );
  }
}

class BookRecommendationPage extends StatefulWidget {
  const BookRecommendationPage({super.key, required this.title});

  final String title;

  @override
  State<BookRecommendationPage> createState() => _BookRecommendationPageState();
}

class _BookRecommendationPageState extends State<BookRecommendationPage> {
  final TextEditingController _controller = TextEditingController();
  List<String> recommendations = [];

Future<void> _getRecommendations() async {
  String query = _controller.text.trim();

  if (query.isEmpty) {
    setState(() {
      recommendations = ["Please enter a genre."];
    });
    return;
  }

  try {
    // Use 10.0.2.2 if running on Android emulator
    final url = Uri.parse("http://10.0.2.2:8000/recommend?query=$query");
    final response = await http.get(url);

    if (response.statusCode == 200) {
      final data = json.decode(response.body) as List;

      setState(() {
        recommendations = data.map((book) => book["title"] as String? ?? "No title").toList();
      });
    } else {
      setState(() {
        recommendations = ["Error: ${response.statusCode}"];
      });
    }
  } catch (e) {
    setState(() {
      recommendations = ["Failed to fetch recommendations: $e"];
    });
  }
}

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(widget.title),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              "Enter a genre (e.g. fantasy, sci-fi, mystery, romance):",
              style: TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _controller,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                hintText: "Type a genre...",
              ),
            ),
            const SizedBox(height: 12),
            ElevatedButton(
              onPressed: _getRecommendations,
              child: const Text("Get Recommendations"),
            ),
            const SizedBox(height: 20),
            Expanded(
              child: recommendations.isEmpty
                  ? const Center(child: Text("No recommendations yet."))
                  : ListView.builder(
                      itemCount: recommendations.length,
                      itemBuilder: (context, index) {
                        return Card(
                          margin: const EdgeInsets.symmetric(vertical: 5),
                          child: ListTile(
                            leading: const Icon(Icons.book, color: Colors.deepPurple),
                            title: Text(recommendations[index]),
                          ),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }
}