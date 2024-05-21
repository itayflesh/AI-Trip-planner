'use client';

import { useState } from 'react';
import axios from 'axios';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
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
  const [startDate, setStartDate] = useState(new Date());
  const [endDate, setEndDate] = useState(new Date());
  const [budget, setBudget] = useState('');
  const [tripType, setTripType] = useState('');
  const [destinationDetails, setDestinationDetails] = useState<DestinationDetails>({});
  const [selectedDestination, setSelectedDestination] = useState('');
  const [dailyPlan, setDailyPlan] = useState('');
  const [tripSummary, setTripSummary] = useState('');
  const [tripImages, setTripImages] = useState<string[]>([]);
  const [showSearchForm, setShowSearchForm] = useState(true);

  const handleGetSuggestions = async () => {
    try {
      const response = await axios.post<{ destination_details: DestinationDetails }>('http://localhost:8000/destinations', {
        start_date: startDate.toISOString().slice(0, 10),
        end_date: endDate.toISOString().slice(0, 10),
        budget: parseFloat(budget),
        trip_type: tripType,
      });
      setDestinationDetails(response.data.destination_details);
      setShowSearchForm(false);
    } catch (error) {
      console.error('Error getting destination suggestions:', error);
    }
  };

  const handleSelectDestination = async (destinationName: string) => {
    setSelectedDestination(destinationName);
    try {
      const response = await axios.post<{ daily_plan: string; summary: string }>('http://localhost:8000/daily-plan', {
        destination_name: destinationName,
        start_date: startDate.toISOString().slice(0, 10),
        end_date: endDate.toISOString().slice(0, 10),
        trip_type: tripType,
      });
      setDailyPlan(response.data.daily_plan);
      setTripSummary(response.data.summary);

      const imagesResponse = await axios.post<{ image_urls: string[] }>('http://localhost:8000/trip-images', {
        destination_name: destinationName,
        trip_month: startDate.toLocaleString('default', { month: 'long' }),
        trip_type: tripType,
        summary: response.data.summary,
      });
      setTripImages(imagesResponse.data.image_urls);
    } catch (error) {
      console.error('Error getting daily plan and trip images:', error);
    }
  };

  const handleNewSearch = () => {
    setStartDate(new Date());
    setEndDate(new Date());
    setBudget('');
    setTripType('');
    setDestinationDetails({});
    setSelectedDestination('');
    setDailyPlan('');
    setTripSummary('');
    setTripImages([]);
    setShowSearchForm(true);
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1 className={styles.title}>Trip Planner</h1>
      </header>
      <main className={styles.main}>
        <section className={styles.searchSection}>
          <div className={styles.searchForm}>
            <div className={styles.formGroup}>
              <label htmlFor="startDate" className={styles.label}>Start Date:</label>
              <DatePicker
                id="startDate"
                selected={startDate}
                onChange={(date: Date) => setStartDate(date)}
                dateFormat="yyyy-MM-dd"
                className={styles.datePicker}
                disabled={!showSearchForm}
              />
            </div>
            <div className={styles.formGroup}>
              <label htmlFor="endDate" className={styles.label}>End Date:</label>
              <DatePicker
                id="endDate"
                selected={endDate}
                onChange={(date: Date) => setEndDate(date)}
                dateFormat="yyyy-MM-dd"
                className={styles.datePicker}
                disabled={!showSearchForm}
              />
            </div>
            <div className={styles.formGroup}>
              <label htmlFor="budget" className={styles.label}>Budget:</label>
              <input
                type="text"
                id="budget"
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
                placeholder="Enter your budget"
                className={styles.input}
                disabled={!showSearchForm}
              />
            </div>
            <div className={styles.formGroup}>
              <label htmlFor="tripType" className={styles.label}>Trip Type:</label>
              <select
                id="tripType"
                value={tripType}
                onChange={(e) => setTripType(e.target.value)}
                className={styles.select}
                disabled={!showSearchForm}
              >
                <option value="">Select trip type</option>
                <option value="ski">Ski</option>
                <option value="beach">Beach</option>
                <option value="city">City</option>
              </select>
            </div>
          </div>
          {showSearchForm ? (
            <button onClick={handleGetSuggestions} className={styles.searchButton}>
              Get Suggestions
            </button>
          ) : (
            <button onClick={handleNewSearch} className={styles.newSearchButton}>
              New Search
            </button>
          )}
        </section>

        {selectedDestination ? (
          <section className={styles.selectedDestinationSection}>
            <h2 className={styles.sectionTitle}>Let's look at your daily plan trip to: {selectedDestination}</h2>
            {dailyPlan && (
              <>
                
                <div className={dailyPlanStyles.dailyPlanContainer}>
                  {dailyPlan.split('Day').filter(Boolean).map((day, index) => {
                    const dayHeader = `Day ${index + 1}`;
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
              <h2 className={styles.sectionTitle}>Here are 5 flight destinations that match your search:</h2>
              <div className={styles.destinationGrid}>
                {Object.entries(destinationDetails).map(([airportCode, details]) => {
                  const destinationName = details.name.replace(/\*/g, '');
                  return (
                    <div key={airportCode} className={styles.destinationCard}>
                      <h3 className={styles.destinationTitle}>{destinationName}</h3>
                      <div className={styles.destinationDetails}>
                        {details.flight_price && (
                          <p className={styles.destinationInfo}>
                            <span className={styles.destinationLabel}>Flight Price:</span> ${details.flight_price}
                          </p>
                        )}
                        {details.hotel_name && (
                          <p className={styles.destinationInfo}>
                            <span className={styles.destinationLabel}>Hotel Name:</span> {details.hotel_name}
                          </p>
                        )}
                        {details.hotel_price && (
                          <p className={styles.destinationInfo}>
                            <span className={styles.destinationLabel}>Hotel Price:</span> ${details.hotel_price}
                          </p>
                        )}
                      </div>
                      <button onClick={() => handleSelectDestination(destinationName)} className={styles.selectButton}>
                        Select Destination
                      </button>
                    </div>
                  );
                })}
              </div>
            </section>
          )
        )}
      </main>
    </div>
  );
};

export default TripPlannerPage;