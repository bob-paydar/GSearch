# GSearch: Google Advanced Search Builder

![GSearch Screenshot](https://github.com/bob-paydar/GSearch/blob/main/Screenshot.png) <!-- Replace with actual screenshot if available -->

## Overview

GSearch is a desktop application built with PyQt6 that allows users to construct advanced Google search queries using various operators and filters. It provides an intuitive graphical interface for building complex searches, previewing the query, and executing it in a web browser. The application supports standard web searches as well as specialized options for images, videos, and news. It includes features like recent query management, example searches, and a dark mode theme.

This application is ideal for researchers, developers, and anyone who frequently uses Google's advanced search capabilities but prefers a dedicated tool over the web interface.

## Features

### Search Query Building
- **All these words**: Enter space-separated terms that must all appear in the results. Choose where they appear (anywhere, title, text, URL, or links).
- **This exact word or phrase**: Specify an exact phrase to be quoted in the query.
- **None of these words**: Exclude space-separated terms with the `-` operator.
- **Any of these words (OR)**: Use `|` to separate alternatives for OR logic.
- **Site or domain**: Limit results to a specific site (e.g., `site:example.com`).
- **File type**: Filter by file extensions (e.g., `pdf`, `docx`).
- **intitle**: Terms that must appear in the page title.
- **inurl**: Terms that must appear in the URL.
- **Numbers ranging from**: Specify a numeric range (e.g., `100..200`) with an optional unit (e.g., `$`).

### Date Range Filtering
- Optional "after" and "before" dates with checkboxes to enable/disable.
- Calendar popups for easy date selection.
- Quick preset buttons: Past 24h, Past week, Past month, Past year.

### Search Types
- **Web**: Standard web search.
- **Images**: Image search with advanced filters (see below).
- **Videos**: Video search.
- **News**: News search.

### Advanced Image Search Options
When "Images" is selected as the search type, additional filters become available:
- **Image size**: Any size, Large, Medium, Icon.
- **Aspect ratio**: Any aspect ratio, Square, Tall, Wide, Panoramic.
- **Colors in image**: Any color, Full color, Black and white, Transparent, or Specific color (e.g., Red, Blue).
- **Type of image**: Any type, Face, Photo, Clip art, Line drawing, Animated.
- **Region**: Any region or specific countries (e.g., United States, United Kingdom).
- **Usage rights**: All, Free to use or share, Free to use or share commercially, etc.

### Preview and Controls
- **Preview query**: Displays the constructed query or URL parameters in real-time.
- **Copy**: Copies the preview to the clipboard (Ctrl+C).
- **Search in browser**: Opens the query in the default web browser (Ctrl+Enter).
- **Save to Recent**: Saves the current query to the recent list (Ctrl+S).
- **Clear all**: Resets all fields.

### Recent Queries
- Stores up to 20 recent queries in `GSearch.ini` (located in the application directory).
- List view with double-click to load.
- Buttons to Load or Delete selected queries.
- Automatically loads recent queries on startup.

### Examples Menu
The "Examples" menu provides 20 pre-configured search examples to demonstrate usage:
1. Find PDFs on example.com
2. Exact phrase + exclude
3. Price range for laptops
4. Recipes with ingredients OR
5. News articles in last month
6. Tutorials in URL
7. Files excluding certain types
8. Books in title
9. Events in specific year range
10. Products in price range with unit
11. Research papers on site
12. Quotes exact phrase
13. Exclude common sites
14. Images filetype
15. Videos in URL
16. All words in text
17. Links to page with anchor
18. Date range for historical events
19. Number range without unit
20. Combined operators

Selecting an example populates the fields automatically.

### Help Menu
- **About**: Displays application information, including version and programmer credit (Bob Paydar).

### Additional Features
- **Dark Mode**: Uses a Fusion style with dark palette for better visibility in low-light environments.
- **Keyboard Shortcuts**: Ctrl+C (Copy), Ctrl+Enter (Search), Ctrl+S (Save to Recent).
- **Persistent Settings**: Recent queries are saved to an INI file and loaded on startup. If the file doesn't exist, it's created automatically.

## Installation

1. Ensure you have Python 3.12+ installed.
2. Install required dependencies:
   ```
   pip install PyQt6
   ```
3. Download the script (`GSearch.py`) and run it:
   ```
   python GSearch.py
   ```

No additional packages are needed beyond PyQt6, as the application uses standard libraries for other functionalities.

## Usage

1. Launch the application.
2. Fill in the desired search criteria using the input fields and dropdowns.
3. Use the date pickers and checkboxes for time-based filtering.
4. Select the search type (Web/Images/Videos/News).
5. If Images is selected, configure additional image-specific filters.
6. View the preview to verify the query.
7. Click "Search in browser" to execute, or save/load from recent queries.
8. Explore examples from the menu to learn advanced usage.

## Configuration

- **Recent Queries File**: `GSearch.ini` in the same directory as the script. This file stores recent searches in a simple key-value format. Delete it to reset history.

## Limitations

- The application does not support all possible Google search operators (e.g., related:, cache:), focusing on the most common advanced ones.
- Image search filters are approximated based on Google's TBS parameters; results may vary.
- No internet connectivity is required to build queries, but executing searches opens a browser.
- Region filtering for images uses a limited set of countries; expand as needed in the code.

## Contributing

Feel free to fork the repository, add features (e.g., more operators, light mode), or report issues. Pull requests are welcome!

## Credits

- Built with PyQt6.
- Programmer: Bob Paydar

## License

This project is open-source under the MIT License. See LICENSE file for details.
