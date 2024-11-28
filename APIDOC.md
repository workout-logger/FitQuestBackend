# FitQuest API Documentation



---

## Endpoints

### **1. Admin**
| Method | Endpoint  | Description            | Request Body |
|--------|-----------|------------------------|--------------|
| GET    | `/admin/` | Admin site dashboard.  | None         |

---

### **2. Authentication**
| Method  | Endpoint                         | Description                                              | Request Body |
|---------|----------------------------------|----------------------------------------------------------|--------------|
| Various | `/api/auth/`                     | Routes to authentication-related APIs (e.g., login).     | Depends on the specific API. |
| Various | `/api/auth/registration/`        | Routes to user registration-related APIs.                | Depends on the specific API. |
| Various | `/accounts/`                     | Routes to account-related APIs from `allauth`.           | Depends on the specific API. |

---

### **3. Social Authentication**
| Method | Endpoint              | Description                                             | Request Body |
|--------|-----------------------|---------------------------------------------------------|--------------|
| Various | `/api/social/`       | Routes to social authentication-related APIs.          | Depends on the specific API. |
| GET    | `/api/social/google/` | Routes to Google social login.                         | None         |

---

### **4. Exercises**
| Method | Endpoint                        | Description                               | Request Body |
|--------|---------------------------------|-------------------------------------------|--------------|
| GET    | `/exercise/?muscle_type=Biceps` | Retrieves all exercises of a muscle group | None         |
| GET    | `/exercise/exercises_all`       | Retrieves all exercises                   | None         |
| GET    | `/muscles`                      | Retrieves all muscle groups               | None         |

---

### **5. Workouts**
#### List and Create Workouts
| Method | Endpoint              | Description                              | Request Body                                                                                                   |
|--------|-----------------------|------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| GET    | `/workouts/`          | Retrieves a list of all workouts for the authenticated user. | None                                                                                                          |
| POST   | `/workouts/`          | Creates a new workout for the authenticated user.            | `{ "duration": <int>, "workout_date": <ISO8601 datetime>, "avg_heart_rate": <float>, "mood": <int>, "energy_burned": <float> }` |

#### Retrieve, Update, and Delete a Workout
| Method | Endpoint              | Description                                                | Request Body                                                                                                       |
|--------|-----------------------|------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| GET    | `/workouts/<int:pk>/` | Retrieves the details of a specific workout.               | None                                                                                                              |
| PUT    | `/workouts/<int:pk>/` | Updates the details of a specific workout.                 | `{ "duration": <int>, "workout_date": <ISO8601 datetime>, "avg_heart_rate": <float>, "mood": <int>, "energy_burned": <float> }` |
| DELETE | `/workouts/<int:pk>/` | Deletes a specific workout.                                | None                                                                                                              |

#### Sync Workouts
| Method | Endpoint              | Description                                                | Request Body                                                                                                                                                                                                                                                                                                                |
|--------|-----------------------|------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| POST   | `/sync_workouts/`     | Synchronizes workout data from external sources.           | `{ "workout_data": [ { "value": { "workoutActivityType": <string>, "totalEnergyBurned": <float> }, "start_date": <ISO8601 datetime>, "end_date": <ISO8601 datetime>, "mood": <int> } ], "heartrate_data": [ { "value": { "numericValue": <int> }, "start_date": <ISO8601 datetime>, "end_date": <ISO8601 datetime> } ] }` |

#### Last Workout
| Method | Endpoint              | Description                                                | Request Body                                                                                                   |
|--------|-----------------------|------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| GET    | `/last_workout/`      | Retrieves the details of the most recent workout.          | None                                                                                                          |

#### Update Muscle Groups
| Method | Endpoint                                  | Description                                                | Request Body                                                                                     |
|--------|------------------------------------------|------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| PATCH  | `/workout/update_latest_muscle_groups/`  | Updates muscle groups associated with the most recent workout. | `{ "muscleGroups": [<string>, <string>, ...] }`                                                |

#### Workouts This Week
| Method | Endpoint              | Description                                                | Request Body                                                                                     |
|--------|-----------------------|------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| GET    | `/week_workouts/`     | Retrieves all workouts for the current week.               | None                                                                                           |

---

### **6. Dungeons**
| Method | Endpoint             | Description                          | Request Body                     |
|--------|-----------------------|--------------------------------------|----------------------------------|
| Various | `/dungeons/`         | Routes to dungeon-related APIs.      | NOT IMPLEMENTED     |

---

### **7. Rewards**
| Method | Endpoint             | Description                          | Request Body                     |
|--------|-----------------------|--------------------------------------|----------------------------------|
| Various | `/rewards/`          | Routes to rewards-related APIs.      | NOT IMPLEMENTED     |

---

### **8. Global Chat**
| Method | Endpoint             | Description                          | Request Body                     |
|--------|-----------------------|--------------------------------------|----------------------------------|
| Various | `/global_chat/`      | Routes to global chat APIs.          | NOT IMPLEMENTED     |

---

### **9. Trading**
| Method | Endpoint             | Description                          | Request Body                     |
|--------|-----------------------|--------------------------------------|----------------------------------|
| Various | `/trading/`          | Routes to trading-related APIs.      | NOT IMPLEMENTED     |
