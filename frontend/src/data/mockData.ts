import type { NewsArticle, NewsSource } from '../types/news';
import type { DashboardData } from '../types/news';
import type { CategoryFilterItem } from '../types/news';

export const australianNewsSources: NewsSource[] = [
  { id: 'abc', name: 'ABC News', url: 'https://www.abc.net.au/news/' },
  { id: 'smh', name: 'Sydney Morning Herald', url: 'https://www.smh.com.au/' },
  { id: 'theage', name: 'The Age', url: 'https://www.theage.com.au/' },
  { id: 'herald-sun', name: 'Herald Sun', url: 'https://www.heraldsun.com.au/' },
  { id: 'courier-mail', name: 'The Courier-Mail', url: 'https://www.couriermail.com.au/' },
  { id: 'australian', name: 'The Australian', url: 'https://www.theaustralian.com.au/' },
  { id: 'news-com-au', name: 'News.com.au', url: 'https://www.news.com.au/' },
  { id: 'nine-news', name: 'Nine News', url: 'https://www.9news.com.au/' }
];

export const categoryFilters: CategoryFilterItem[] = [
  { category: 'music', label: 'Music', color: '#8B5CF6' },
  { category: 'lifestyle', label: 'Lifestyle', color: '#10B981' },
  { category: 'finance', label: 'Finance', color: '#F59E0B' },
  { category: 'sports', label: 'Sports', color: '#EF4444' }
];

const mockArticles: NewsArticle[] = [
  {
    id: '1',
    title: 'Tame Impala Announces New Australian Tour Dates',
    summary: 'Perth psychedelic rock band Tame Impala has announced additional Australian tour dates for 2024.',
    content: 'Full article content here...',
    category: 'music',
    source: 'ABC News',
    author: 'Sarah Mitchell',
    publishedAt: '2024-03-15T10:30:00Z',
    url: 'https://abc.net.au/news/tame-impala-tour',
    highlights: [
      'New tour dates include Sydney, Melbourne, and Brisbane',
      'Tickets go on sale Friday at 9am',
      'Special guest performers to be announced'
    ]
  },
  {
    id: '2',
    title: 'ASX 200 Reaches New Record High Amid Mining Boom',
    summary: 'The Australian stock market has hit a new record high driven by strong mining sector performance.',
    content: 'Full article content here...',
    category: 'finance',
    source: 'Sydney Morning Herald',
    author: 'James Chen',
    publishedAt: '2024-03-15T09:15:00Z',
    url: 'https://smh.com.au/finance/asx-record',
    highlights: [
      'ASX 200 closes at 7,890 points',
      'Iron ore prices surge 15% this week',
      'Banking sector also shows strong gains'
    ]
  },
  {
    id: '3',
    title: 'AFL Season Preview: Richmond Tigers Ready for Comeback',
    summary: 'Richmond Tigers look to bounce back after disappointing 2023 season with new recruits.',
    content: 'Full article content here...',
    category: 'sports',
    source: 'Herald Sun',
    author: 'Mark Robinson',
    publishedAt: '2024-03-15T08:45:00Z',
    url: 'https://heraldsun.com.au/sport/afl-richmond',
    highlights: [
      'Three new star recruits join the squad',
      'Pre-season form shows promising signs',
      'Coach optimistic about finals chances'
    ]
  },
  {
    id: '4',
    title: 'Melbourne Food Festival Showcases Australian Cuisine',
    summary: 'The annual Melbourne Food and Wine Festival celebrates the best of Australian culinary talent.',
    content: 'Full article content here...',
    category: 'lifestyle',
    source: 'The Age',
    author: 'Emma Thompson',
    publishedAt: '2024-03-15T07:20:00Z',
    url: 'https://theage.com.au/lifestyle/food-festival',
    highlights: [
      'Over 200 restaurants participating',
      'Focus on indigenous Australian ingredients',
      'Celebrity chef masterclasses available'
    ]
  },
  {
    id: '5',
    title: 'Hilltop Hoods Win ARIA Award for Best Hip Hop Release',
    summary: 'Adelaide hip hop group Hilltop Hoods takes home another ARIA award for their latest album.',
    content: 'Full article content here...',
    category: 'music',
    source: 'News.com.au',
    author: 'Lisa Parker',
    publishedAt: '2024-03-14T18:30:00Z',
    url: 'https://news.com.au/music/hilltop-hoods-aria',
    highlights: [
      'Fifth ARIA award for the group',
      'Album topped charts for 3 consecutive weeks',
      'National tour planned for later this year'
    ]
  },
  {
    id: '6',
    title: 'Reserve Bank Keeps Interest Rates Steady at 4.35%',
    summary: 'RBA maintains current interest rate amid ongoing inflation concerns.',
    content: 'Full article content here...',
    category: 'finance',
    source: 'The Australian',
    author: 'David Walsh',
    publishedAt: '2024-03-14T16:45:00Z',
    url: 'https://theaustralian.com.au/finance/rba-rates',
    highlights: [
      'Decision unanimous among board members',
      'Inflation showing signs of stabilization',
      'Next review scheduled for April'
    ]
  },
  {
    id: '7',
    title: 'NRL Round 3: Panthers Maintain Perfect Start',
    summary: 'Penrith Panthers continue their winning streak with dominant performance against Raiders.',
    content: 'Full article content here...',
    category: 'sports',
    source: 'Nine News',
    author: 'Michael Stevens',
    publishedAt: '2024-03-14T15:20:00Z',
    url: 'https://9news.com.au/sport/nrl-panthers',
    highlights: [
      'Panthers win 32-12 at home',
      'Nathan Cleary scores two tries',
      'Team extends winning streak to 8 games'
    ]
  },
  {
    id: '8',
    title: 'Sustainable Living: Australian Cities Lead Green Initiative',
    summary: 'Major Australian cities implement new sustainability programs to reduce carbon footprint.',
    content: 'Full article content here...',
    category: 'lifestyle',
    source: 'ABC News',
    author: 'Rachel Green',
    publishedAt: '2024-03-14T12:15:00Z',
    url: 'https://abc.net.au/news/sustainable-cities',
    highlights: [
      'Solar panel installations increase 40%',
      'New bike sharing programs launched',
      'Zero waste initiatives in CBD areas'
    ]
  },
  {
    id: '9',
    title: 'Cryptocurrency Regulations: New Framework Announced',
    summary: 'Australian government unveils comprehensive cryptocurrency regulation framework.',
    content: 'Full article content here...',
    category: 'finance',
    source: 'Sydney Morning Herald',
    author: 'Andrew Kim',
    publishedAt: '2024-03-14T11:30:00Z',
    url: 'https://smh.com.au/finance/crypto-regulations',
    highlights: [
      'New licensing requirements for exchanges',
      'Consumer protection measures strengthened',
      'Implementation begins in July 2024'
    ]
  },
  {
    id: '10',
    title: 'Commonwealth Games 2026: Brisbane Preparations Underway',
    summary: 'Brisbane gears up for the 2026 Commonwealth Games with venue construction and planning.',
    content: 'Full article content here...',
    category: 'sports',
    source: 'The Courier-Mail',
    author: 'Sophie Turner',
    publishedAt: '2024-03-14T10:45:00Z',
    url: 'https://couriermail.com.au/sport/commonwealth-games',
    highlights: [
      'Main stadium construction 60% complete',
      'Volunteer recruitment program launched',
      'Transport infrastructure upgrades planned'
    ]
  }
];

export const mockDashboardData: DashboardData = {
  topArticles: mockArticles.slice(0, 10),
  categories: {
    music: mockArticles.filter(article => article.category === 'music'),
    lifestyle: mockArticles.filter(article => article.category === 'lifestyle'),
    finance: mockArticles.filter(article => article.category === 'finance'),
    sports: mockArticles.filter(article => article.category === 'sports')
  },
  sources: australianNewsSources
};