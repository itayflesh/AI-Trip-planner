'use client';

import { useState } from 'react';
import axios from 'axios';
import styles from './TripPlanner.module.css';
import dailyPlanStyles from './DailyPlan.module.css';

interface DestinationDetails {
  [key: string]: {
    name: string;
    flight_price?: number;
    hotel_name?: string;
    hotel_price?: number;
    message?: string;
  };
}

const TripPlannerPage = () => {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [budget, setBudget] = useState('');
  const [tripType, setTripType] = useState('');
  const [destinationDetails, setDestinationDetails] = useState<DestinationDetails>({});
  const [selectedDestination, setSelectedDestination] = useState('');
  const [dailyPlan, setDailyPlan] = useState('');
  const [tripSummary, setTripSummary] = useState('');
  const [tripImages, setTripImages] = useState<string[]>([]);

  const handleGetSuggestions = async () => {
    try {
      const response = await axios.post<{ destination_details: DestinationDetails }>('http://localhost:8000/destinations', {
        start_date: startDate,
        end_date: endDate,
        budget: parseFloat(budget),
        trip_type: tripType,
      });
      setDestinationDetails(response.data.destination_details);
    } catch (error) {
      console.error('Error getting destination suggestions:', error);
    }
  };

  const handleSelectDestination = async (destinationName: string) => {
    setSelectedDestination(destinationName);
    try {
      const response = await axios.post<{ daily_plan: string; summary: string }>('http://localhost:8000/daily-plan', {
        destination_name: destinationName,
        start_date: startDate,
        end_date: endDate,
        trip_type: tripType,
      });
      setDailyPlan(response.data.daily_plan);
      setTripSummary(response.data.summary);

      const imagesResponse = await axios.post<{ image_urls: string[] }>('http://localhost:8000/trip-images', {
        destination_name: destinationName,
        trip_month: new Date(startDate).toLocaleString('default', { month: 'long' }),
        trip_type: tripType,
        summary: response.data.summary,
      });
      setTripImages(imagesResponse.data.image_urls);
    } catch (error) {
      console.error('Error getting daily plan and trip images:', error);
    }
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1 className={styles.title}>Trip Planner</h1>
      </header>
      <main className={styles.main}>
        <section className={styles.formSection}>
          <div className={styles.inputGroup}>
            <label htmlFor="startDate" className={styles.label}>Start Date:</label>
            <input
              type="text"
              id="startDate"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              placeholder="YYYY-MM-DD"
              className={styles.input}
            />
          </div>
          <div className={styles.inputGroup}>
            <label htmlFor="endDate" className={styles.label}>End Date:</label>
            <input
              type="text"
              id="endDate"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              placeholder="YYYY-MM-DD"
              className={styles.input}
            />
          </div>
          <div className={styles.inputGroup}>
            <label htmlFor="budget" className={styles.label}>Budget:</label>
            <input
              type="text"
              id="budget"
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
              placeholder="$"
              className={styles.input}
            />
          </div>
          <div className={styles.inputGroup}>
            <label htmlFor="tripType" className={styles.label}>Trip Type:</label>
            <input
              type="text"
              id="tripType"
              value={tripType}
              onChange={(e) => setTripType(e.target.value)}
              placeholder="ski/beach/city..."
              className={styles.input}
            />
          </div>
          <button onClick={handleGetSuggestions} className={styles.button}>Get Suggestions</button>
        </section>

        {selectedDestination ? (
  <section className={styles.selectedDestinationSection}>
    <h2 className={styles.sectionTitle}>Selected Destination: {selectedDestination}</h2>
    {dailyPlan && (
      <>
        <h3 className={styles.subtitle}>Daily Plan:</h3>
        <div className={dailyPlanStyles.dailyPlanContainer}>
          {dailyPlan.split('Day').filter(Boolean).map((day, index) => {
            const dayHeader = `Day ${index + 1}:`;
            const activities = day.trim().split('- ').slice(1);
            return (
              <div key={index} className={dailyPlanStyles.dayCard}>
                <div className={dailyPlanStyles.dayHeader}>{dayHeader}</div>
                <div className={dailyPlanStyles.dayActivities}>
                  {activities.map((activity, activityIndex) => (
                    <div key={activityIndex} className={styles.destinationInfo}>
                      - {activity.trim()}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </>
    )}
    {tripImages.length > 0 && (
      <div className={styles.tripImages}>
        <h3 className={styles.subtitle}>Trip Images:</h3>
        <div className={styles.imageGrid}>
          {tripImages.map((imageUrl, index) => (
            <img key={index} src={imageUrl} alt={`Trip Image ${index + 1}`} className={styles.image} />
          ))}
        </div>
      </div>
    )}
  </section>
        ) : (
          Object.keys(destinationDetails).length > 0 && (
            <section className={styles.destinationSection}>
              <h2 className={styles.sectionTitle}>Destination Details</h2>
              <div className={styles.destinationGrid}>
                {Object.entries(destinationDetails).map(([airportCode, details]) => {
                  // Remove all asterisks from the destination name
                  const destinationName = details.name.replace(/\*/g, '');

                  return (
                    <div key={airportCode} className={styles.destinationCard}>
                      <h3 className={styles.destinationTitle}>{destinationName}</h3>
                      <div className={styles.destinationDetails}>
                        {details.flight_price && (
                          <p className={styles.destinationInfo}>Flight Price: ${details.flight_price}</p>
                        )}
                        {details.hotel_name && (
                          <p className={styles.destinationInfo}>Hotel Name: {details.hotel_name}</p>
                        )}
                        {details.hotel_price && (
                          <p className={styles.destinationInfo}>Hotel Price: ${details.hotel_price}</p>
                        )}
                        {details.message && (
                          <p className={styles.destinationMessage}>{details.message}</p>
                        )}
                      </div>
                      <button onClick={() => handleSelectDestination(destinationName)} className={styles.selectButton}>Select Destination</button>
                    </div>
                  );
                })}
              </div>
            </section>
          )
        )}
      </main>
      <footer className={styles.footer}>
        <p className={styles.footerText}>&copy; 2023 Trip Planner. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default TripPlannerPage;