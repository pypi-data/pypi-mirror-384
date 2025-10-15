# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2025-01-17

### Added

#### Embeddings Service - Enhanced Message Formats

- **Multiple Input Formats**: `remember()` now accepts three formats:
  - Simple strings: `"User likes Python"` (backward compatible)
  - List of dictionaries: `[{"role": "user", "content": "..."}]`
    (mem0 native format)
  - Pydantic models: `[Mem0Message(role="user", content="...")]`
    (type-safe with validation)
- **Conversation Context Support**: Full support for mem0's conversation
  analysis by passing complete message histories

### Changed

#### Embeddings Service API

- **Breaking**: `remember()` parameter renamed from `content: str` to
  `messages: MessageInput`
  - **Migration**: Simple rename: `content="text"` → `messages="text"`
  - **100% Backward Compatible**: All existing string-based code
    continues to work

## [0.2.0] - 2025-10-14

### Added

#### User Summaries Service (NEW)

- **AI-Powered User Profiling**: Automatically generate and maintain
  comprehensive user summaries using LLM
- **Intelligent User Understanding**: Extract user preferences, behavior
  patterns, and contextual information from conversations
- **Smart Action Detection**: Identify and track user actions (preferences,
  facts, behaviors) with automatic categorization
- **Prompt Module System**: Flexible, composable prompts for user summary
  generation
- **Multi-Adapter Support**:
  - MongoDB adapter with optimized indexing for production
  - In-memory adapter for testing and development

#### Docker Example

- **Complete Demo Application**: Full working example with Docker Compose
- **MongoDB Integration**: Pre-configured MongoDB setup for development
- **Environment Configuration**: Example `env.example` file with all required
  variables
- **Multi-Service Orchestration**: Demonstrates Messages, Embeddings, and
  UserSummaries services working together

### Changed

- **Messages MongoDB Adapter**: Enhanced with improved connection handling
  and index optimization
- **Module Structure**: Renamed `usersummaries` to `users_summaries` for
  consistency with Python naming conventions

### Improvements

- **MongoDB Authentication**: Simplified Docker setup with proper connection
  string format
- **Environment Variables**: Cleaned up redundant configuration in Docker
  Compose

## [0.1.1] - 2025-09-19

### Added - Type Support

- **Typing Support**: Added `py.typed` marker file to expose inline type
  hints to type checkers (PEP 561).

### Improvements - Type Checking

- **Strict Type Checking**: Resolved `mypy --strict` errors by:
  - Casting Mem0 response lists in `Mem0Adapter` for accurate types.
  - Ensuring ID extraction returns `str`.

## [0.1.0] - 2025-01-17

### Initial Release

First public release of Dory - AI Memory & Conversation Management Library.

### Features

#### Messages Service

- **Conversation Management**: Automatic conversation reuse within 2-week
  window
- **Message Persistence**: Store user messages and AI responses with full
  async support
- **LangChain/LangGraph Integration**: Export chat history in compatible
  format
- **MongoDB Adapter**: Production-ready MongoDB integration with proper
  indexing
- **In-Memory Adapter**: For testing and development
- **Type Safety**: Full type hints and Pydantic models

#### Embeddings Service (NEW)

- **Memory Storage**: Store and retrieve contextual memories with LLM
  processing
- **Vector Search**: Semantic similarity search for relevant information
- **Raw Embeddings**: Store unprocessed content for retrieval tasks
- **Multiple Backends**:
  - Chroma (local vector store)
  - MongoDB Atlas (with vector search)
  - In-memory (for testing)
- **Powered by Mem0**: Built on top of the robust Mem0 library
- **OpenAI Integration**: Default embedding provider with configurable options

### Acknowledgments

- Built on top of [Mem0](https://github.com/mem0ai/mem0) for embeddings

---

This is the first public release. We welcome feedback and contributions!

[0.2.1]: https://github.com/kopiloto/dory/releases/tag/v0.2.1
[0.2.0]: https://github.com/kopiloto/dory/releases/tag/v0.2.0
[0.1.1]: https://github.com/kopiloto/dory/releases/tag/v0.1.1
[0.1.0]: https://github.com/kopiloto/dory/releases/tag/v0.1.0
