# Contractor Portal

A local web-based contractor portal for managing jobs, schedules, and contractor profiles.

## Features

- **Dashboard**: Overview of active jobs, completed jobs, today's schedule, and notifications
- **Jobs Management**: View, search, filter, and update job status
- **Schedule Calendar**: Weekly calendar view of scheduled jobs
- **Profile Management**: Update contractor profile information and view certifications

## Project Structure

```
contractor-portal/
├── index.html          # Main HTML file
├── css/
│   ├── styles.css      # Main styles (layout, components)
│   └── components.css  # Reusable component styles (buttons, forms, modals)
├── js/
│   ├── data.js         # Sample data and data helper functions
│   └── app.js          # Main application logic
└── README.md           # This file
```

## Getting Started

### Option 1: Open directly in browser
Simply open `index.html` in your web browser.

### Option 2: Use a local server
For a better development experience, use a local server:

```bash
# Using Python
python -m http.server 8080

# Using Node.js (npx)
npx serve .

# Using VS Code Live Server extension
# Right-click index.html → Open with Live Server
```

Then navigate to `http://localhost:8080` in your browser.

## Features Overview

### Dashboard
- View key statistics (active jobs, completed jobs, etc.)
- See today's scheduled appointments
- View recent notifications

### Jobs
- Browse all jobs with search and filter capabilities
- Click on any job to view details
- Update job status (Pending → In Progress → Completed)

### Schedule
- Weekly calendar view
- Visual representation of scheduled jobs
- Navigate between weeks (coming soon)

### Profile
- Update personal information
- View and manage certifications

## Customization

### Adding New Jobs
Edit `js/data.js` and add new job objects to the `sampleJobs` array.

### Styling
- Modify CSS variables in `css/styles.css` to change colors, spacing, etc.
- Component-specific styles are in `css/components.css`

### API Integration
The application is designed to work with sample data but can be easily extended to fetch data from an API:

1. Replace the sample data functions in `data.js` with API calls
2. Use `fetch()` or a library like Axios to make HTTP requests
3. Update the UI rendering functions in `app.js` to handle async data loading

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

MIT License - Feel free to use and modify as needed.
