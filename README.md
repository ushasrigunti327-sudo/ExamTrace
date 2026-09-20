# ExamTrace

## Evidence-Based Examination Monitoring & Integrity Analysis System

### Project Overview

ExamTrace is a web-based examination monitoring and integrity analysis system developed to support secure and structured online examinations. It combines online assessment functionality with webcam-based monitoring, browser activity monitoring, event logging, evidence capture, integrity scoring, risk classification, analytics, and reporting.

The system records relevant examination events and provides structured information that can assist authorized administrators or invigilators in reviewing examination sessions.

### Problem Statement

Online examinations provide flexibility and accessibility, but maintaining examination integrity in remote environments can be challenging. Traditional online examination systems mainly focus on candidate authentication, questions, answers, timers, and submission, while providing limited monitoring and evidence for reviewing examination events.

ExamTrace addresses this requirement by integrating online assessment with continuous examination monitoring and integrity analysis.

### Objectives

- Develop a web-based online examination platform.
- Provide candidate registration and authentication.
- Validate camera availability before the examination.
- Monitor candidate presence using webcam-based face detection.
- Detect no-face and multiple-face conditions.
- Monitor browser-related activities.
- Detect focus loss and fullscreen exit events.
- Record examination monitoring events.
- Capture supporting evidence snapshots.
- Calculate an integrity score based on configured monitoring events.
- Classify examination sessions into configured risk levels.
- Provide examination and session analytics.
- Generate integrity analysis reports.

### Key Features

- Candidate Registration
- Candidate Login
- Candidate Photo Capture
- Online MCQ Examination
- Examination Timer
- Camera Validation
- Webcam Face Monitoring
- No-Face Detection
- Multiple-Face Detection
- Tab Switch Monitoring
- Focus Loss Monitoring
- Fullscreen Monitoring
- Violation/Event Logging
- Evidence Snapshot Capture
- Integrity Score Calculation
- Risk Classification
- Session Analytics
- Integrity Reporting
- Administrator/Invigilator Review

### System Workflow

Candidate Registration  
↓  
Candidate Login  
↓  
Candidate Verification  
↓  
Camera Validation  
↓  
Online Examination  
↓  
Continuous Monitoring  
↓  
Event Detection  
↓  
Event and Evidence Logging  
↓  
Integrity Analysis  
↓  
Risk Classification  
↓  
Analytics and Reporting

### System Modules

#### 1. Candidate Authentication

Provides candidate registration, login, session management, and controlled access to the examination system.

#### 2. Candidate Management

Maintains candidate information and associates the candidate with the corresponding examination session.

#### 3. Online Assessment

Provides MCQ-based examination functionality including question display, answer selection, question navigation, timer management, and submission.

#### 4. Camera Validation

Checks webcam availability before the examination begins to ensure that the required monitoring environment is available.

#### 5. Face Monitoring

Uses OpenCV-based computer vision to monitor candidate presence and identify conditions such as no face detected and multiple faces detected.

#### 6. Browser Activity Monitoring

Monitors supported browser-related examination events such as tab switching, focus loss, and fullscreen exit.

#### 7. Violation and Event Management

Records detected monitoring events and associates them with the corresponding examination session.

#### 8. Evidence Capture

Captures supporting snapshots for relevant monitoring events to provide additional information during examination review.

#### 9. Integrity Analysis

Processes recorded examination events and calculates an integrity score using configured rules and event weights.

#### 10. Risk Classification

Classifies examination sessions into configured risk categories based on the integrity analysis results.

#### 11. Analytics

Provides structured analysis of examination sessions, monitoring events, integrity scores, and risk information.

#### 12. Reporting

Provides consolidated examination and integrity information for authorized review, including session details, monitoring events, scores, risk information, and supporting evidence.

### Technologies Used

- Python
- Flask
- OpenCV
- SQLite
- HTML
- CSS
- JavaScript
- Pandas
- Scikit-learn
- Matplotlib
- Seaborn
- LangChain / AI-assisted reporting where implemented

### Project Structure

```text
ExamTrace/
│
├── app.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
│
├── templates/
├── static/
├── docs/
│
└── other project source files


Testing

The system was tested using functional test cases covering:

Candidate Registration
Candidate Login
Pre-assessment Camera Validation
No-Face Detection
Multiple-Face Detection
MCQ Answer Selection
Question Navigation
Mark for Review
Tab Switch Monitoring
Focus Loss Monitoring
Fullscreen Exit Monitoring
Integrity Score Calculation
Risk Classification
Evidence Snapshot Capture
Analytics Generation
Integrity Report Generation
Documentation

The docs folder contains the project documentation and testing deliverables:

Agile Documentation
General Project Documentation
Agile Template
Defect Tracker
Unit Test Plan
Security and Privacy

The system uses authentication and session-based access to manage examination activities. Monitoring events and supporting evidence are associated with examination sessions for structured review.

For deployment, appropriate access control, secure credential management, protected configuration, and suitable data-retention practices should be followed.

Future Scope
Advanced candidate identity verification
Improved computer vision-based monitoring
Behavioural anomaly detection
Real-time invigilator dashboard
Cloud-based deployment
Advanced examination analytics
Enhanced evidence management
Improved AI-assisted integrity reporting
Scalable support for multiple examinations and institutions
Conclusion

ExamTrace integrates online examination functionality with examination monitoring and integrity analysis. By combining candidate authentication, webcam monitoring, browser activity monitoring, event logging, evidence capture, integrity scoring, risk classification, analytics, and reporting, the system provides structured information to support authorized examination review.

The project demonstrates the application of Python, Flask, OpenCV, SQLite, web technologies, and data-analysis techniques in developing an integrated examination monitoring system.
