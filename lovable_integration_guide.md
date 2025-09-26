# Query Visibility Checker - Lovable Integration Guide

## 🚀 Quick Setup

### 1. Add the HTML Structure
Copy the content from `query_visibility_html.html` and paste it into your Lovable dashboard's Query Visibility Checker section.

### 2. Add the CSS Styles
Copy the content from `query_visibility_styles.css` and add it to your Lovable dashboard's global styles or component styles.

### 3. Add the JavaScript
Copy the content from `frontend_integration.js` and add it to your Lovable dashboard's JavaScript section.

## 🔧 Configuration

### API Endpoint
The JavaScript is configured to use:
```javascript
const API_BASE_URL = 'https://web-production-a5831.up.railway.app';
```

### Required HTML Data Attributes
Make sure your HTML has these data attributes:
- `data-input="domain"` - on the domain input field
- `data-action="get-company-info"` - on the "Get Company Information" button
- `data-step="brand"`, `data-step="queries"`, `data-step="results"` - on each step container
- `data-step-indicator="1"`, `data-step-indicator="2"`, etc. - on step indicators

## 🎨 Customization

### Colors
The CSS uses your existing purple theme:
- Primary: `#8B5CF6` (Purple)
- Secondary: `#A855F7` (Light Purple)
- Success: `#10B981` (Green)
- Error: `#EF4444` (Red)

### Responsive Design
The interface is fully responsive and will work on mobile devices.

## 🔄 How It Works

1. **User enters domain** → Triggers `startAnalysis()`
2. **Calls `/query-check` endpoint** → Gets brand context and query analysis
3. **Updates UI step by step** → Shows progress through Domain → Brand → Queries → Results
4. **Displays actionable recommendations** → Shows what the user needs to do

## 📊 Data Flow

```
User Input (Domain) 
    ↓
Frontend JavaScript
    ↓
POST /query-check
    ↓
Backend Analysis (ScrapingBee + OpenAI)
    ↓
Structured Response
    ↓
Frontend Display (4 Steps)
```

## 🛠️ Troubleshooting

### Common Issues

1. **CORS Errors**: Make sure your Lovable domain is added to the CORS origins in `main.py`
2. **API Errors**: Check the browser console for detailed error messages
3. **Styling Issues**: Make sure the CSS is loaded and not conflicting with existing styles

### Debug Mode
The JavaScript includes console logging. Check the browser console for:
- API request/response data
- Step transitions
- Error messages

## 🎯 Features

### ✅ What Works
- Domain input validation
- Automatic brand context extraction
- Query generation and analysis
- Step-by-step progress indication
- Responsive design
- Error handling

### 🔮 Future Enhancements
- Custom query input
- Export results
- Save analysis history
- Advanced filtering options

## 📱 Mobile Support
The interface is fully responsive and includes:
- Stacked step indicators on mobile
- Single-column layouts
- Touch-friendly buttons
- Readable text sizes

## 🎨 Styling Notes
- Uses CSS Grid and Flexbox for layouts
- Includes smooth animations and transitions
- Matches your existing purple theme
- Includes loading states and error handling
- Fully accessible with proper ARIA labels
