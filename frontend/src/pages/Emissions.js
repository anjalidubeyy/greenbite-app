import React, { useState, useEffect, useMemo } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Bar, Pie } from "react-chartjs-2";
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement } from "chart.js";
import axios from 'axios';
import "../styles/Emissions.css";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement);

const Emissions = () => {
    const navigate = useNavigate();
    const location = useLocation();
    
    const state = location.state || {};
    console.log("Location state:", state); // Debug state
    const recipeName = state.recipeName || "Emissions Report";
    console.log("Recipe name:", recipeName); // Debug recipe name

    const emissionsData = useMemo(() => state.emissionsData || { breakdown: {}, total_emissions: 0 }, [state.emissionsData]);
    const selectedIngredients = useMemo(() => state.selectedIngredients || [], [state.selectedIngredients]);

    const [error, setError] = useState(null);
    const [sustainabilityScore, setSustainabilityScore] = useState(null);

    useEffect(() => {
        if (!state.recipeName) {
            setError("Missing recipe data. Please try again.");
            return;
        }

        const requestData = {
            ingredients: selectedIngredients,
            land_use_change: emissionsData.breakdown["Land Use Change"] || 0,
            feed: emissionsData.breakdown["Feed"] || 0,
            farm: emissionsData.breakdown["Farm"] || 0,
            processing: emissionsData.breakdown["Processing"] || 0,
            transport: emissionsData.breakdown["Transport"] || 0,
            packaging: emissionsData.breakdown["Packaging"] || 0,
            retail: emissionsData.breakdown["Retail"] || 0,
            total_land_to_retail: emissionsData.breakdown["Total from Land to Retail"] || 0,
        };

        console.log("Sending emissions data to predict endpoint:", requestData); // Debug log

        const fetchSustainabilityScore = async () => {
            try {
                const response = await axios.post('https://greenbite-api.onrender.com/predict', requestData);
                // Cap the score at 5.0 and format it to 1 decimal place
                const score = response.data.sustainability_score;
                const cappedScore = typeof score === 'number' ? Math.min(5.0, score) : 3.0;
                setSustainabilityScore(cappedScore.toFixed(1));
            } catch (error) {
                console.error('Error fetching sustainability score:', error);
                setSustainabilityScore('Error');
            }
        };

        fetchSustainabilityScore();
    }, [state.recipeName, emissionsData, selectedIngredients]);

    const emissionsBreakdown = emissionsData.breakdown;
    const emissionsEquivalence = emissionsData.emissions_equivalence || {
        car_distance: 0,
        smartphone_charges: 0,
        plastic_bags: 0,
        led_bulb_hours: 0
    };

    // Remove total emissions from the breakdown for the charts
    const filteredBreakdown = Object.entries(emissionsBreakdown).filter(([key, value]) => key !== "Total Emissions");
    const chartData = {
        labels: filteredBreakdown.map(([key]) => key),
        datasets: [
            {
                label: "Emissions (kg CO2)",
                data: filteredBreakdown.map(([, value]) => value),
                backgroundColor: ["#A2D2FF", "#FFAFCC", "#BDE0FE", "#FFBE98", "#B5E48C", "#FFCFD2"],
            },
        ],
    };

    // Function to determine color based on sustainability score
    const getScoreColor = (score) => {
        // Convert score to number if it's a string
        const numericScore = typeof score === 'string' ? parseFloat(score) : score;
        
        // Ensure score is capped at 5.0
        const cappedScore = Math.min(5.0, numericScore);
        
        if (cappedScore >= 4.5) return "#2d6a4f"; // Green ✅
        if (cappedScore >= 3.5) return "#52b788"; // Light Green 🟢
        if (cappedScore >= 2.5) return "#ffcc00"; // Yellow 🟡
        if (cappedScore >= 1.5) return "#ff7f50"; // Orange 🟠
        return "#d9534f"; // Red 🔴
    };

    return (
        <div className="emissions-container">
            <h2>Emissions Report</h2>

            {error ? (
                <p className="error">{error}</p>
            ) : (
                <div className="emissions-content">
                    {/* Left Side: Sustainability Score */}
                    <div className="sustainability-score-container">
                        <h3>Sustainability Score</h3>
                        <div 
                            className="sustainability-score"
                            style={{ color: getScoreColor(sustainabilityScore) }}
                        >
                            {sustainabilityScore !== null ? sustainabilityScore : 'Calculating...'}
                        </div>
                    </div>

                    {/* Right Side: Emissions Data */}
                    <div className="emissions-data">
                        <h3>Emissions Breakdown</h3>
                        <ul>
                            {Object.entries(emissionsBreakdown).map(([key, value], index) => (
                                key !== "Total Emissions" && (
                                    <li key={index}>
                                        <strong>{key}:</strong> {value} kg CO2
                                    </li>
                                )
                            ))}
                        </ul>
                    </div>
                </div>
            )}

            {/* Real-Life Emissions Equivalence */}
            <div className="emissions-equivalence">
                <h3>Real-Life Emissions Equivalence</h3>
                <div className="equivalence-grid">
                    <div className="equivalence-item">
                        <span className="equivalence-icon">🚗</span>
                        <div className="equivalence-details">
                            <h4>Car Distance</h4>
                            <p>{emissionsEquivalence.car_distance} km</p>
                        </div>
                    </div>
                    <div className="equivalence-item">
                        <span className="equivalence-icon">📱</span>
                        <div className="equivalence-details">
                            <h4>Smartphone Charges</h4>
                            <p>{emissionsEquivalence.smartphone_charges} charges</p>
                        </div>
                    </div>
                    <div className="equivalence-item">
                        <span className="equivalence-icon">🛍️</span>
                        <div className="equivalence-details">
                            <h4>Plastic Bags</h4>
                            <p>{emissionsEquivalence.plastic_bags} bags</p>
                        </div>
                    </div>
                    <div className="equivalence-item">
                        <span className="equivalence-icon">💡</span>
                        <div className="equivalence-details">
                            <h4>LED Bulb Hours</h4>
                            <p>{emissionsEquivalence.led_bulb_hours} hours</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Charts */}
            <div className="emissions-chart">
                <div className="chart-container">
                    <h3>Bar Chart: Emissions by Category</h3>
                    <Bar data={chartData} options={{ responsive: true, plugins: { title: { display: true, text: "Emissions Breakdown" } } }} />
                </div>

                <div className="chart-container">
                    <h3>Pie Chart: Emissions Distribution</h3>
                    <Pie data={chartData} options={{ responsive: true, plugins: { title: { display: true, text: "Emissions Distribution" } } }} />
                </div>
            </div>

            <button onClick={() => navigate("/")}>Back to Search</button>
        </div>
    );
};

export default Emissions;
