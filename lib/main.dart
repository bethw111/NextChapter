//import statements
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

//root container
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'NextChapter',
      debugShowCheckedModeBanner: false, 
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
        scaffoldBackgroundColor: Colors.grey[100],
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
  bool isLoading = false;

  //default dropdown values
  String selectedMood = "Adventurous";
  String selectedGenre = "Fantasy";
  String pace = "Fast";
  String length = "Medium";

  final TextEditingController favouriteBooksController =
      TextEditingController();
  final TextEditingController recentReadsController =
      TextEditingController();

  List<Map<String, dynamic>>bookSuggestions = [];
  Map<String, dynamic >? selectedBook;
  List<Map<String, dynamic>> recommendations = [];

  Future<void> sendFeedback(Map<String, dynamic> book, int label) async {
    final url = Uri.parse("http://127.0.0.1:8000/feedback");

    try {
      await http.post(
        url,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "favourite_book": selectedBook?["title"] ?? "",
          "recommended_book": book["title"] ?? "",
          "genre": selectedGenre,
          "mood": selectedMood,
          "pace": pace,
          "length": length,
          "features": book["features"],
          "label": label,
        }),
      );
    } catch (e) {
      print("feedback error: $e");
    }
  }

//help page text
  void showHelpDialog(){
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text("How to use NextChapter"),
          content: const Text(
            "Use this page to find recommendations tailored to you! \n\n"
            "Select your preferences from the dropdowns shown in line with what you want to read next. \n\n"
            "Be sure to select your favourite book, or one similar to what you are looking for next. \n\n"
            "Then click 'Get Recommendations' and wait for your new favourite reads to appear. \n\n"
            "Enjoy reading and discovering!",
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text("Got it"),
            ),
          ],
        );
      },
    );
  }

  Future<void> searchBooks(String query) async {
    if (query.length < 3) {
      setState(() {
        bookSuggestions = [];
      });
      return;
    }

    final url = Uri.parse(
      "https://www.googleapis.com/books/v1/volumes?q=${Uri.encodeComponent(query)}&maxResults=5");

    try {
      final response = await http.get(url);
      print("status: ${response.statusCode}");
      print("body: ${response.body}");
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final items = data["items"] as List? ?? [];

        setState(() {
          bookSuggestions = items.map((item) {
            final info = item["volumeInfo"];
            final title = info["title"] as String? ?? "Unknown title";
            final authors = (info["authors"] as List?)?.join(", ")?? "Unknown author";
            return {
              "title": title,
              "authors": authors,
              };
          }).toList();
        });
      }
    } catch (e) {}
  }

  //calls FASTAPI
  Future<void> _getRecommendations() async {

    if (selectedBook == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Please search for and select a book first")),
      );
      return;
    }

    final url = Uri.parse("http://127.0.0.1:8000/recommend_by_preferences");

    setState(() => isLoading = true);

    try {
      final response = await http.post(
        url,
        headers: {"Content-Type": "application/json"},
        //convert dart map to JSON
        body: jsonEncode({
          "mood": selectedMood,
          "genre": selectedGenre,
          "favourite_books": selectedBook!["title"],
          "recent_reads": recentReadsController.text,
          "pace": pace,
          "length": length
        }),
      );

      if (response.statusCode == 200) {
        //final data = json.decode(response.body) as List;
        final decoded = json.decode(response.body);
        final List data = decoded is List ? decoded : decoded["recommendations"] ?? [];

        setState(() {
          //extract titles and convert to list of strings
          recommendations = List<Map<String, dynamic>>.from(
            data.map((book) => {
            "title": book["title"] as String? ?? "No title",
            "authors": (book["authors"] as List?)?.join(", ") ?? "Unknown",
            "explanation": book["explanation"] ?? {},
            "features": book["features"],
          }),
          );
        });
      //error handling
      } else {
        setState(() {
          recommendations = [{"title": "Error: ${response.statusCode}", "authors": ""}];
        });
      }
    } catch (e) {
      setState(() {
        recommendations = [{"title": "Failed to fetch recommendations: $e", "authors": ""}];
      });
    }
    setState(() => isLoading = false);
  }

  Widget sectionCard({required Widget child}) {
    return Card(
      elevation: 2,
      margin: const EdgeInsets.symmetric(vertical: 8),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: Padding(padding: const EdgeInsets.all(16), child: child),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(widget.title),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.help_outline),
            onPressed: showHelpDialog,
          )
        ],
      ),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  Container(
                      width: 48,
                      height: 48,
                      decoration: BoxDecoration(
                        color: Colors.deepPurple,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Icon(Icons.menu_book,
                          color: Colors.white),
                    ),
                    const SizedBox(width: 12),
                    const  Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text("NextChapter",
                            style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                            color: Colors.black87
                          )),
                        Text("Find your next read",
                          style: TextStyle(color: Colors.grey)
                        ),
                      ],
                    )
                    ),
                  ],
                ),

              const SizedBox(height: 24),

              const Text("Preferences", 
                style: TextStyle(fontWeight: FontWeight.bold)),

              const SizedBox(height: 10),

            //form dropdown options and UI updates
              DropdownButtonFormField<String>(
                value: selectedMood,
                decoration: const InputDecoration(
                  labelText: " Select Mood", 
                  filled: true,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.all(Radius.circular(12)),
                  ),
                ),
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
            
            const SizedBox(height: 12),

            DropdownButtonFormField<String>(
              value: selectedGenre,
              decoration:
                  const InputDecoration(
                    labelText: "Select Favourite Genre",
                    filled: true,
                    border:OutlineInputBorder(
                      borderRadius: BorderRadius.all(Radius.circular(12)),
                    ),
                  ),
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
            const SizedBox(height: 20),

            //form text inputs
            TextField(
              controller: favouriteBooksController,
              decoration: InputDecoration(
                labelText: "Search for a Favourite Book",
                filled: true,
                border: const OutlineInputBorder(
                  borderRadius: BorderRadius.all(Radius.circular(12)),
                ),
                suffixIcon: selectedBook != null
                    ? IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          setState(() {
                            selectedBook = null;
                            favouriteBooksController.clear();
                            bookSuggestions = [];
                          });
                        },
                    )
                    : const Icon(Icons.search),
              ),
              onChanged: (value) {
                if (selectedBook != null) {
                  setState(() => selectedBook = null);
                }
                searchBooks(value);
              },
            ),

            if (bookSuggestions.isNotEmpty && selectedBook == null)
              Material(
                elevation: 2,
                borderRadius: BorderRadius.circular(12),
                child: ListView.builder(
                  shrinkWrap: true,
                  itemCount: bookSuggestions.length,
                  itemBuilder: (context, index) {
                    final book = bookSuggestions[index];
                    return ListTile(
                      //leading: const Icon(Icons.book, color: Colors.deepPurple),
                      title: Text(book["title"]!),
                      subtitle: Text(book["authors"]!),
                      onTap: () {
                        setState(() {
                          selectedBook = book;
                          favouriteBooksController.text = book["title"]!;
                          bookSuggestions = [];
                        });
                      },  
                    );
                  },
                ),
              ),

              if (selectedBook != null)
                Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: Chip(
                    avatar: const Icon(Icons.check, size: 16, color: Colors.white),
                    label: Text(selectedBook!["title"]!),
                    backgroundColor: Colors.deepPurple,
                    labelStyle: const TextStyle(color: Colors.white),
              ),
            ),

            const SizedBox(height: 16),

            //TextField(
            //  controller: recentReadsController,
            //  decoration: const InputDecoration(
            //    labelText: "Recent Reads",
            //    filled: true,
            //    border: OutlineInputBorder(
            //      borderRadius: BorderRadius.all(Radius.circular(12)),
            //    ),
            //  ),
            //),

            const SizedBox(height: 12),

            DropdownButtonFormField<String>(
              value: pace,
              decoration:
                  const InputDecoration(
                    labelText: "Select a Preferred Pace",
                    filled: true,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.all(Radius.circular(12)),
                    ),
                  ),
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

            const SizedBox(height: 12),

            DropdownButtonFormField<String>(
              value: length,
              decoration:
                  const InputDecoration(
                    labelText: "Select a Preferred Length",
                    filled: true,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.all(Radius.circular(12)),
                    ),
                  ),
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

            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _getRecommendations,
                style: ElevatedButton.styleFrom(
                  padding:
                    const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              child: const Text("Get Recommendations"),
            ),
            ),

            const SizedBox(height: 20),

            //recommendations loading and view
            isLoading
            ? const Center(child: CircularProgressIndicator())
            : recommendations.isEmpty
                  ? const Center(
                      child: Text("No recommendations yet."),
                    )
                  : ListView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                      itemCount: recommendations.length,
                      itemBuilder: (context, index) {
                        return Card(
                          elevation: 4,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          margin: const EdgeInsets.symmetric(vertical: 8),
                          child: ListTile(
                            contentPadding: const EdgeInsets.all(12),

                            leading:
                              const Icon(Icons.book, color: Colors.deepPurple,),

                            title: Text(
                              recommendations[index]["title"] ?? "No title",
                              style: const TextStyle(fontWeight: FontWeight.bold)
                              ),

                            subtitle: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(recommendations[index]["authors"] ?? "Unknown"),
                                const SizedBox(height: 4),

                                Builder(
                                  builder: (context) {
                                    final explanation =
                                      (recommendations[index]["explanation"] is Map) ? recommendations[index]["explanation"] as Map: {};

                                    //tells the user why the book was recommended
                                    return Text(
                                      "Why this was recommended for you: "
                                      "${explanation["genre_match"] == true ? "Genre match • " : ""}"
                                      "${explanation["same_author"] == true ? "Same author • " : ""}"
                                      "${explanation["matched_mood"] == true ? "Fits your mood • " : ""}"
                                      "${explanation["matched_pace"] == true ? "Right pace • " : ""}"
                                      "${explanation["matched_length"] == true ? "Good length • " : ""}"
                                      "Similar content",
                                      style: TextStyle(
                                        fontSize: 12,
                                        color: Colors.grey[600],
                                      ),
                                    );
                                  },
                                ),

                                const SizedBox(height: 8),

                                Row(
                                  children: [
                                    IconButton(
                                      icon: const Icon(
                                        Icons.thumb_up_alt_outlined,
                                        color: Colors.green,
                                      ),
                                      onPressed: () {
                                        sendFeedback(recommendations[index], 1);
                                        ScaffoldMessenger.of(context).showSnackBar(
                                          const SnackBar(content: Text("liked")),
                                        );
                                      }
                                    ),
                                    IconButton(
                                      icon: const Icon(
                                        Icons.thumb_down_alt_outlined,
                                        color: Colors.red,
                                      ),
                                    onPressed: () {
                                        sendFeedback(recommendations[index], 0);
                                        ScaffoldMessenger.of(context).showSnackBar(
                                          const SnackBar(content: Text("disliked")),
                                        );
                                    },
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
            ],
          ),
        ),
      ),
    );
  }
}