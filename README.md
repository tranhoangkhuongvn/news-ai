# Australian News AI Dashboard

An intelligent news aggregation system that scrapes articles from major Australian news sources, applies AI-powered classification and similarity detection, and presents the most important stories through smart prioritization. The system extracts content from ABC News, The Guardian Australia, Sydney Morning Herald, and News.com.au across sports, finance, lifestyle, and music categories. Using advanced algorithms, it identifies breaking news, clusters related articles across sources, and ranks stories by importance using multi-factor scoring. The platform provides both traditional article browsing and an enhanced "Smart News Discovery" feature that surfaces the top 10 most significant stories with comprehensive metadata and priority analysis.

## Frontend Features

**🌐 Deployed URL**: [https://cool-news-ai-app-2qwl5.ondigitalocean.app](https://cool-news-ai-app-2qwl5.ondigitalocean.app)

The React-based dashboard provides an intuitive interface for accessing Australian news with the following features:

### Main Interface
- **Dashboard Overview**: View top articles from all sources with category filtering
- **Real-time Data**: Live connection to backend API with health status indicators
- **Responsive Design**: Clean, modern interface optimized for desktop and mobile

### News Discovery Options
1. **Get Latest News**: Extract fresh articles from all 4 sources (~80-160 articles in 1-2 minutes)
2. **Smart News Discovery**: AI-powered extraction and prioritization (320 articles → top 10 stories in 3-5 minutes)

### Enhanced Story Display
- **Priority Badges**: Visual indicators for BREAKING, HIGH, MEDIUM, and LOW priority stories
- **Source Coverage**: See which outlets are covering each story
- **Urgency Keywords**: Highlighted breaking news indicators
- **Priority Scores**: Detailed breakdown of breaking news, coverage, and quality metrics
- **Time Analysis**: Human-readable time descriptions and geographic scope

### User Interaction
1. **Browse Articles**: Use category filters to explore news by topic
2. **Refresh Data**: Click refresh button for latest cached articles
3. **Extract Fresh News**: Use "Get Latest News" for comprehensive multi-source updates
4. **Discover Priority Stories**: Click "Smart News Discovery" for AI-curated top stories
5. **Read Articles**: Click any story card to open the original article

### Notes:
The deployed backend does not have the AI capability yet, we intend to update the deployment VM for the backend. Please refer to the local host version for the AI feature.
![hippo](./News_Dashboard.gif)

## Local Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup
```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI server
python run_api.py
# API will be available at http://localhost:8000
```

### Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
# Frontend will be available at http://localhost:5173
```

### Verify Setup
1. Backend API docs: http://localhost:8000/docs
2. Health check: http://localhost:8000/health
3. Frontend dashboard: http://localhost:5173

## Todo List

### Immediate Improvements
- [ ] Add user authentication and personalized news preferences
- [ ] Implement article bookmarking and reading history
- [ ] Add email/push notifications for breaking news alerts
- [ ] Create mobile app with React Native

### Enhanced Features
- [ ] Multi-language support and international news sources
- [ ] Social media integration for trending topic analysis
- [ ] Advanced filtering by keywords, date ranges, and custom categories
- [ ] Export functionality for articles (PDF, email, social sharing)

### Technical Enhancements
- [ ] Implement Redis caching for improved performance
- [ ] Add comprehensive test coverage (unit, integration, e2e)
- [ ] Set up CI/CD pipeline with automated deployments
- [ ] Database migration to PostgreSQL for production scaling
- [ ] Add monitoring and analytics dashboard

### AI & ML Improvements
- [ ] Enhanced sentiment analysis for article tone detection
- [ ] Personalized recommendation engine based on reading patterns
- [ ] Automatic article summarization using advanced NLP
- [ ] Trend prediction and news cycle analysis
- [ ] Fact-checking integration with external verification services

### Infrastructure
- [ ] Docker containerization for easy deployment
- [ ] Kubernetes orchestration for scalability
- [ ] Load balancing for high availability
- [ ] Automated backups and disaster recovery
- [ ] Performance monitoring and alerting system