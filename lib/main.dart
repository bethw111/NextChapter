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
  State<BookRecommendationPage> createState() =>
      _BookRecommendationPageState();
}

class _BookRecommendationPageState extends State<BookRecommendationPage> {
  String selectedMood = "Adventurous";
  String selectedGenre = "Fantasy";
  String pace = "Fast";
  String length = "Medium";

  final TextEditingController favoriteBooksController =
      TextEditingController();
  final TextEditingController recentReadsController =
      TextEditingController();

  List<String> recommendations = [];

  Future<void> _getRecommendations() async {
    final url = Uri.parse("http://127.0.0.1:8000/recommend_by_preferences");

    try {
      final response = await http.post(
        url,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "mood": selectedMood,
          "genre": selectedGenre,
          "favorite_books": favoriteBooksController.text,
          "recent_reads": recentReadsController.text,
          "pace": pace,
          "length": length
        }),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body) as List;

        setState(() {
          recommendations = data
              .map((book) =>
                  book["title"] as String? ?? "No title available")
              .toList();
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
            DropdownButtonFormField<String>(
              value: selectedMood,
              decoration: const InputDecoration(labelText: "Mood"),
              items: [
                "Adventurous",
                "Dark",
                "Romantic",
                "Inspirational",
                "Mysterious"
              ]
                  .map((mood) =>
                      DropdownMenuItem(value: mood, child: Text(mood)))
                  .toList(),
              onChanged: (value) {
                setState(() {
                  selectedMood = value!;
                });
              },
            ),
            const SizedBox(height: 10),

            DropdownButtonFormField<String>(
              value: selectedGenre,
              decoration:
                  const InputDecoration(labelText: "Favorite Genre"),
              items: [
                "Fantasy",
                "Sci-Fi",
                "Mystery",
                "Romance",
                "Thriller",
                "Non-Fiction"
              ]
                  .map((genre) =>
                      DropdownMenuItem(value: genre, child: Text(genre)))
                  .toList(),
              onChanged: (value) {
                setState(() {
                  selectedGenre = value!;
                });
              },
            ),
            const SizedBox(height: 10),

            TextField(
              controller: favoriteBooksController,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                labelText: "Favorite Books (comma separated)",
              ),
            ),
            const SizedBox(height: 10),

            TextField(
              controller: recentReadsController,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                labelText: "Recent Reads (comma separated)",
              ),
            ),
            const SizedBox(height: 10),

            DropdownButtonFormField<String>(
              value: pace,
              decoration:
                  const InputDecoration(labelText: "Preferred Pace"),
              items: ["Fast", "Medium", "Slow"]
                  .map((p) =>
                      DropdownMenuItem(value: p, child: Text(p)))
                  .toList(),
              onChanged: (value) {
                setState(() {
                  pace = value!;
                });
              },
            ),
            const SizedBox(height: 10),

            DropdownButtonFormField<String>(
              value: length,
              decoration:
                  const InputDecoration(labelText: "Preferred Length"),
              items: ["Short", "Medium", "Long"]
                  .map((l) =>
                      DropdownMenuItem(value: l, child: Text(l)))
                  .toList(),
              onChanged: (value) {
                setState(() {
                  length = value!;
                });
              },
            ),
            const SizedBox(height: 20),

            ElevatedButton(
              onPressed: _getRecommendations,
              child: const Text("Get Recommendations"),
            ),
            const SizedBox(height: 20),

            Expanded(
              child: recommendations.isEmpty
                  ? const Center(
                      child: Text("No recommendations yet."),
                    )
                  : ListView.builder(
                      itemCount: recommendations.length,
                      itemBuilder: (context, index) {
                        return Card(
                          margin: const EdgeInsets.symmetric(
                              vertical: 5),
                          child: ListTile(
                            leading: const Icon(
                              Icons.book,
                              color: Colors.deepPurple,
                            ),
                            title:
                                Text(recommendations[index]),
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