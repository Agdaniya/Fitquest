from firebase_admin import initialize_app, credentials, firestore

# Initialize Firebase Admin SDK
cred = credentials.Certificate('F:\\s8\\Fitquest\\fitquest-9b891-firebase-adminsdk-bhy5p-2469ae19c9.json')
initialize_app(cred)

# Get Firestore client
db = firestore.client()

# Define exercises by fitness level
exercises = {
    'Beginner': [
        {
            'name': 'Jumping Jacks',
            'description': 'Improves cardiovascular fitness and coordination.',
            'sets': 3,
            'reps': 20,
            'rest': '30 sec',
            'image': 'asset/jj.png'
        },
        {
            'name': 'Wall Push-ups',
            'description': 'Builds upper body strength with less intensity.',
            'sets': 3,
            'reps': 10,
            'rest': '45 sec',
            'image': 'asset/wall-pushup.png'
        },
        {
            'name': 'Knee Planks',
            'description': 'Builds core strength with modified plank.',
            'sets': 3,
            'duration': '20 sec',
            'rest': '30 sec',
            'image': 'asset/knee-plank.png'
        }
    ],
    'Intermediate': [
        {
            'name': 'Push-ups',
            'description': 'Builds upper body and core strength.',
            'sets': 3,
            'reps': '10-15',
            'rest': '60 sec',
            'image': 'asset/pushup.png'
        },
        {
            'name': 'Squats',
            'description': 'Builds lower body strength and core stability.',
            'sets': 3,
            'reps': 15,
            'rest': '45 sec',
            'image': 'asset/squat.png'
        },
        {
            'name': 'Planks',
            'description': 'Strengthens core, improves posture and balance.',
            'sets': 3,
            'duration': '30 sec',
            'rest': '30 sec',
            'image': 'asset/planks.png'
        }
    ],
    'Advanced': [
        {
            'name': 'Burpees',
            'description': 'Full-body high-intensity exercise.',
            'sets': 4,
            'reps': 15,
            'rest': '45 sec',
            'image': 'asset/burpees.png'
        },
        {
            'name': 'Pistol Squats',
            'description': 'Advanced single-leg squat for strength and balance.',
            'sets': 3,
            'reps': 10,
            'rest': '60 sec',
            'image': 'asset/pistol-squat.png'
        },
        {
            'name': 'Plyometric Push-ups',
            'description': 'Explosive push-ups for advanced upper body power.',
            'sets': 3,
            'reps': '8-12',
            'rest': '90 sec',
            'image': 'asset/plyo-pushup.png'
        }
    ]
}

# Populate Firestore with exercises
for level, exercise_list in exercises.items():
    level_ref = db.collection('exercises').document(level)
    level_ref.set({
        'exercises': exercise_list
    })

print("Exercises successfully populated in Firestore!")