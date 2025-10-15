# Architecture Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE LAYER                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐  │
│   │  CLI     │      │  main.py │      │ examples │      │  Custom  │  │
│   │  (cli.py)│      │          │      │   .py    │      │   Code   │  │
│   └─────┬────┘      └────┬─────┘      └────┬─────┘      └────┬─────┘  │
│         │                │                  │                 │        │
│         └────────────────┴──────────────────┴─────────────────┘        │
│                                    │                                    │
└────────────────────────────────────┼────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          FACTORY LAYER                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                      ┌───────────────────────┐                         │
│                      │   CrawlerFactory      │                         │
│                      │                       │                         │
│                      │ ┌───────────────────┐ │                         │
│                      │ │ create_crawler    │ │                         │
│                      │ │ create_youtube    │ │                         │
│                      │ │ create_soundcloud │ │                         │
│                      │ └───────────────────┘ │                         │
│                      └───────────┬───────────┘                         │
│                                  │                                     │
│        ┌────────────┬────────────┼────────────┬────────────┐          │
│        │            │            │            │            │          │
│        ▼            ▼            ▼            ▼            ▼          │
│   ┌─────────┐  ┌────────┐  ┌─────────┐  ┌────────┐  ┌──────────┐    │
│   │Database │  │WebDriver│ │Download │  │  Link  │  │  State   │    │
│   │ Factory │  │ Factory │  │ Manager │  │Extract.│  │ Manager  │    │
│   │         │  │         │  │ Factory │  │Factory │  │          │    │
│   └────┬────┘  └────┬────┘  └────┬────┘  └────┬───┘  └────┬─────┘    │
└────────┼────────────┼────────────┼────────────┼───────────┼───────────┘
         │            │            │            │           │
         │            │            │            │           │
         ▼            ▼            ▼            ▼           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          BUSINESS LOGIC LAYER                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                        ┌──────────────────┐                            │
│                        │     CRAWLER      │                            │
│                        │                  │                            │
│                        │  ┌────────────┐  │                            │
│                        │  │   crawl()  │  │                            │
│                        │  │   close()  │  │                            │
│                        │  │ get_stats()│  │                            │
│                        │  └────────────┘  │                            │
│                        └────────┬─────────┘                            │
│                                 │                                      │
│          ┌──────────────────────┼──────────────────────┐               │
│          │          │           │           │          │               │
│          ▼          ▼           ▼           ▼          ▼               │
│     ┌─────────┐ ┌──────┐  ┌─────────┐ ┌────────┐ ┌────────┐          │
│     │IDatabase│ │IWeb  │  │Download │ │ ILink  │ │ State  │          │
│     │         │ │Driver│  │ Manager │ │Extract.│ │Manager │          │
│     └────┬────┘ └──┬───┘  └────┬────┘ └────┬───┘ └────┬───┘          │
└──────────┼─────────┼───────────┼───────────┼──────────┼───────────────┘
           │         │           │           │          │
           ▼         ▼           ▼           ▼          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       IMPLEMENTATION LAYER                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐  ┌────────────┐  ┌─────────────┐  ┌──────────────┐  │
│  │   SQLite     │  │  Selenium  │  │   YtDlp     │  │   YouTube    │  │
│  │   Database   │  │  WebDriver │  │   Download  │  │     Link     │  │
│  │              │  │            │  │   Strategy  │  │  Extractor   │  │
│  └──────────────┘  └────────────┘  └─────────────┘  └──────────────┘  │
│                                                                         │
│  ┌──────────────┐                                   ┌──────────────┐  │
│  │  PostgreSQL  │                                   │  SoundCloud  │  │
│  │  Database    │                                   │     Link     │  │
│  │  (future)    │                                   │  Extractor   │  │
│  └──────────────┘                                   └──────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
           │         │           │           │          │
           ▼         ▼           ▼           ▼          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          DATA/INFRASTRUCTURE                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────┐   ┌────────────┐   ┌──────────┐   ┌────────────────┐  │
│  │  SQLite   │   │   Chrome   │   │  yt-dlp  │   │  State Files   │  │
│  │  Database │   │  Browser   │   │  Library │   │     (.json)    │  │
│  │   (.db)   │   │  (Selenium)│   │          │   │                │  │
│  └───────────┘   └────────────┘   └──────────┘   └────────────────┘  │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                    Download Folder                                │ │
│  │                    (MP3/Audio Files)                              │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘


                          CONFIGURATION LAYER
                                  │
                ┌─────────────────┴─────────────────┐
                │     ApplicationConfig             │
                │                                   │
                │  ┌───────────────┐                │
                │  │ Platform      │                │
                │  │ Crawler       │                │
                │  │ Database      │                │
                │  │ Download      │                │
                │  │ Selenium      │                │
                │  └───────────────┘                │
                └───────────────────────────────────┘
```

## Component Interaction Flow

```
User Request
     │
     ▼
┌─────────────────┐
│  Factory        │  Creates all components with proper configuration
│  creates        │
│  Crawler        │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                         CRAWLER                                 │
│                                                                 │
│  1. Load State        ────►  StateManager.load_state()         │
│  2. Pop URL from queue                                          │
│  3. Load Page         ────►  WebDriver.get_page_source()       │
│  4. Extract Links     ────►  LinkExtractor.extract_*()         │
│  5. Check Downloaded  ────►  Database.is_downloaded()          │
│  6. Download Content  ────►  DownloadManager.download()        │
│  7. Save to DB        ────►  Database.save_track()             │
│  8. Mark Downloaded   ────►  Database.mark_downloaded()        │
│  9. Queue New Links                                             │
│ 10. Save State        ────►  StateManager.save_state()         │
│ 11. Repeat until queue empty                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Design Patterns Used

```
┌─────────────────────────────────────────────────────────────────┐
│                      STRATEGY PATTERN                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   IDownloadStrategy          ILinkExtractor                    │
│         △                           △                          │
│         │                           │                          │
│    ┌────┴────┐                 ┌───┴───┐                       │
│    │         │                 │       │                       │
│  YtDlp   Aria2            YouTube  SoundCloud                  │
│                                                                 │
│  Allows switching download/extraction strategies at runtime    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      FACTORY PATTERN                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   CrawlerFactory.create_crawler(config, urls)                  │
│          │                                                      │
│          ├──► DatabaseFactory.create_database()                │
│          ├──► WebDriverFactory.create_driver()                 │
│          ├──► DownloadManagerFactory.create_manager()          │
│          ├──► LinkExtractorFactory.create_extractor()          │
│          └──► StateManager()                                    │
│                                                                 │
│  Encapsulates complex object creation logic                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                 DEPENDENCY INJECTION                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Crawler(database, webdriver, downloader, extractor, ...)     │
│                                                                 │
│   All dependencies injected via constructor                    │
│   → Easy to test with mocks                                    │
│   → No hidden dependencies                                     │
│   → Clear dependency graph                                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                 TEMPLATE METHOD PATTERN                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   BaseLinkExtractor (abstract)                                 │
│         │                                                       │
│         ├──► _is_valid_domain() [common]                       │
│         ├──► _should_ignore() [common]                         │
│         ├──► extract_content_links() [override]                │
│         └──► extract_navigation_links() [override]             │
│                                                                 │
│   Common behavior in base, specific in subclasses              │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
                    ┌──────────────────┐
                    │   Start URLs     │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Crawler Queue   │
                    └────────┬─────────┘
                             │
                             ▼
         ┌───────────────────────────────────────┐
         │                                       │
    Depth 0                                 Depth 1, 2, ...
         │                                       │
         ▼                                       ▼
┌──────────────────┐                    ┌──────────────────┐
│  Load Page       │                    │  Load Page       │
│  (WebDriver)     │                    │  (WebDriver)     │
└────────┬─────────┘                    └────────┬─────────┘
         │                                       │
         ▼                                       ▼
┌──────────────────┐                    ┌──────────────────┐
│  Extract Links   │                    │  Extract Links   │
│  (LinkExtractor) │                    │  (LinkExtractor) │
└────────┬─────────┘                    └────────┬─────────┘
         │                                       │
         ├──────► Content Links                 ├──────► Content Links
         │        (download)                    │        (download)
         │             │                        │             │
         │             ▼                        │             ▼
         │      ┌──────────────┐                │      ┌──────────────┐
         │      │  Download    │                │      │  Download    │
         │      │  (Parallel)  │                │      │  (Parallel)  │
         │      └──────┬───────┘                │      └──────┬───────┘
         │             │                        │             │
         │             ▼                        │             ▼
         │      ┌──────────────┐                │      ┌──────────────┐
         │      │  Save to DB  │                │      │  Save to DB  │
         │      └──────────────┘                │      └──────────────┘
         │                                      │
         └──────► Navigation Links              └──────► Navigation Links
                 (add to queue)                         (add to queue)
                       │                                      │
                       └──────────────┬───────────────────────┘
                                      │
                                      ▼
                             ┌──────────────────┐
                             │  Save State      │
                             │  Continue Loop   │
                             └──────────────────┘
```

## SOLID Principles Implementation

```
┌──────────────────────────────────────────────────────────────────────┐
│ Single Responsibility Principle (SRP)                                │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Database       → Only handles data persistence                     │
│  WebDriver      → Only handles browser automation                   │
│  Downloader     → Only handles downloads                            │
│  LinkExtractor  → Only extracts/validates links                     │
│  StateManager   → Only manages state                                │
│  Crawler        → Only orchestrates the crawl                       │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ Open/Closed Principle (OCP)                                          │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Open for extension:  Add new platforms by implementing interfaces  │
│  Closed for modification: Don't change existing platform code       │
│                                                                      │
│  Example: Add Spotify without modifying YouTube code                │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ Liskov Substitution Principle (LSP)                                  │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Any IDatabase implementation can replace another                   │
│  Any IWebDriver implementation can replace another                  │
│  Any IDownloadStrategy implementation can replace another           │
│                                                                      │
│  SQLiteDatabase ←→ PostgreSQLDatabase (drop-in replacement)         │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ Interface Segregation Principle (ISP)                                │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Small, focused interfaces:                                         │
│    - IDatabase: save, is_downloaded, mark_downloaded, get, close    │
│    - IWebDriver: get_page_source, close                            │
│    - IDownloadStrategy: download                                    │
│    - ILinkExtractor: extract_content_links, extract_nav_links      │
│                                                                      │
│  Clients only depend on methods they actually use                   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ Dependency Inversion Principle (DIP)                                 │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  High-level Crawler depends on abstractions (interfaces):           │
│    - IDatabase (not SQLiteDatabase)                                 │
│    - IWebDriver (not SeleniumWebDriver)                             │
│    - IDownloadStrategy (not YtDlpDownloadStrategy)                  │
│                                                                      │
│  Low-level modules implement these abstractions                     │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

This architecture provides:
- **Modularity**: Each component is independent
- **Testability**: Easy to mock and test
- **Extensibility**: Easy to add new features
- **Maintainability**: Clear structure and responsibilities
- **Flexibility**: User has full control over configuration
