# Live Streaming Design (TikTok-like flow)

This document outlines the UX and backend considerations to make the library's Live feature feel like a streamlined, low-friction experience (similar to consumer apps like TikTok).

## High-level UX
- Quick start: users (admins/teachers) can open a simple "Prepare Live" screen with only a title and optional thumbnail/description.
- Single-tap "Go Live": minimal friction to start streaming immediately.
- Pre-fillable title: when starting from other pages, prefill the title for convenience.
- Real-time viewer count and chat: show live viewers and chat with moderation (mute/block, remove messages).
- Persistent recording: after the stream ends, recording is saved automatically and becomes a library `Content` item (with metadata, tags, category).
- Publish controls: Admins can edit, tag, categorize, and publish (or unpublish) the saved recording.

## Fields / Controls (on the setup screen)
- Title (required): short and descriptive.
- Description (optional): short summary for on-demand viewers and metadata.
- Thumbnail/Cover (optional): small image to represent the stream in listings.
- Audience/Privacy toggle: Public or Private (members only).
- Stream key (generated): shown only to the host (used for external RTMP/WebRTC encoders).
- Scheduling (optional): schedule start time to prepare or notify users.

## TikTok-like considerations
- Very low friction to start streaming (one screen, minimal options).
- Visible, real-time viewer metrics and engagement (likes, comments) while live.
- Built-in moderation tools to manage chat (mute, remove, ban) without leaving the stream.
- Quick saving of the recording and immediate availability for on-demand playback with optional downloads.
- For professional use: provide options for higher-quality ingest (RTMP/WebRTC), secure per-stream keys, and CDN storage for recordings.

## Backend capabilities
- Assign secure per-session stream keys (short-lived or revokable).
- Support RTMP/WebRTC ingestion and finalization of recordings (either via in-house recorder service or third-party provider).
- Store recording files under `uploads/live/` and create `Content` records from them.
- Emit real-time events via SocketIO for session lifecycle (started/ended/recording-uploaded) and viewer metrics.

## Next steps (implementation roadmap)
1. Add low-latency WebRTC/RTMP ingest via a stream server (Janus/mediasoup) or managed provider.
2. Add live chat UI and moderation hooks (SocketIO events + admin moderator controls).
3. Add viewer metrics & session analytics to the admin live page.
4. Add scheduling UI and notifications when sessions go live.

---
This design keeps the UX fast and focused while allowing future expansion toward richer engagement features.