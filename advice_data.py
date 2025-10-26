import random

# advise dictionary lists for age group 18-21 people

advise_18_21 = {0:{"High": [ #anxiety column
            "High anxiety detected — consider mindfulness or talking to a counselor.",
            "Your anxiety is high — try relaxation exercises or meditation.",
            "Feeling anxious? Take short breaks and practice deep breathing.",
            "Stress levels are high — journaling your thoughts may help."
        ], 
        "Medium": [
            "Moderate anxiety — maintain balance and practice small stress relief habits.",
            "Keep monitoring your stress, and do small relaxation routines."
        ],
          "Low": [
            "Anxiety level is low — keep up your positive coping habits.",
            "You seem calm — continue your healthy mental habits."
        ]
        },
        6:{"High": [  #sleep quality column
            "Improve your sleep quality — maintain a regular sleep schedule.",
            "Poor sleep can increase stress — focus on rest and relaxation.",
            "Try going to bed and waking up at the same time daily."
        ],
        "Medium": [
            "Sleep is moderate — try keeping a consistent bedtime.",
            "Your sleep is okay, but consistency helps reduce stress."
        ],
        "Low": [
            "Great sleep habits! Keep following your routine.",
            "You’re sleeping well — continue maintaining healthy sleep patterns."
        ]
    },
     13: {      # Study load column
        "High": [
            "Your study load seems heavy — try managing time better.",
            "Take regular short breaks during study sessions to reduce stress."
        ],
        "Medium": [
            "Study load is moderate — maintain balance with breaks.",
            "Keep balancing study and rest — it helps mental clarity."
        ],
        "Low": [
            "Good time management for studies — keep it up!",
            "Your workload is well-balanced — continue your routine."
        ]
    },
     19: {  # Bullying / Peer Pressure
        "High": [
            "You may be facing social stress — seek support if needed.",
            "Try discussing challenges with friends or mentors to reduce stress."
        ],
        "Medium": [
            "Moderate peer pressure — maintain a supportive circle.",
            "Keep a healthy social circle to manage stress effectively."
        ],
        "Low": [
            "You have a healthy social environment — keep it positive.",
            "Great social support — continue engaging with your peers positively."
        ]
    },
     14:{ "High": [ #Academmic performance column
        "Academic performance is causing stress — try planning study sessions better.",
        "High pressure from academics — break tasks into smaller parts."
    ],
    "Medium": [
        "Your academic load is moderate — maintain a good balance between study and rest."
    ],
    "Low": [
        "Great academic habits! Keep managing your workload effectively."
    ]},
    15:{ "High": [ #career concern column
        "High career anxiety — focus on skill building and planning next steps.",
        "Feeling worried about your career? Try talking to a mentor."
    ],
    "Medium": [
        "Moderate career concerns — stay proactive but don’t stress too much."
    ],
    "Low": [
        "You have a positive outlook on your career — keep it up!"
    ]}

    }

# advise dictionary lists for age group 22-60 people
advise_22_60 ={
    0:{#sleep duration column
        "High": [
            "Increase your sleep duration for better health.",
            "Try to get at least 7-8 hours of sleep nightly.",
            "Poor sleep increases stress — maintain a regular sleep schedule."
        ],
        "Medium": [
            "Sleep is moderate — keep a consistent sleep schedule.",
            "Your sleep is okay — minor improvements can help reduce stress."
        ],
        "Low": [
            "Excellent sleep habits — continue your routine.",
            "You sleep well — keep it up for mental clarity."
        ]
    },

    9:{
        # Physical Activity
        "High": [
            "Incorporate regular physical activity into your routine.",
            "Even short daily walks can reduce stress and improve mood.",
            "Try moderate exercises to release tension and relax."
        ],
        "Medium": [
            "Moderate activity — maintain consistency.",
            "Keep active to maintain balance in your daily routine."
        ],
        "Low": [
            "Great activity level — keep it up!",
            "Excellent physical habits — continue your routine for well-being."
        ]
    },

    10: { #screen time column
        
        "High": [
            "Reduce excessive screen time to lower stress.",
            "Too much screen exposure can increase stress — take breaks often.",
            "Consider limiting phone and computer usage in the evening."
        ],
        "Medium": [
            "Screen time is moderate — take regular breaks.",
            "Maintain balanced screen usage for better mental health."
        ],
        "Low": [
            "Excellent screen habits — keep it minimal.",
            "Your low screen exposure is helping you stay calm and focused."
        ]
     
    

    },
    11:{ # Caffeine Intake column
        "High": [
            "Consider reducing caffeine intake for better stress management.",
            "High caffeine can increase anxiety — try limiting coffee or tea."
        ],
        "Medium": [
            "Caffeine intake is moderate — maintain balance.",
            "Your caffeine habits are okay — no major changes needed."
        ],
        "Low": [
            "Caffeine consumption is low — great job!",
            "Low caffeine helps maintain calm and stable energy levels."
        ]

    },
    17:{# Meditation Practice
        "High": [
            "Start or increase meditation practice to reduce stress.",
            "Meditation helps relax the mind — try daily sessions."
        ],
        "Medium": [
            "Moderate meditation — try maintaining a routine.",
            "Keep meditating regularly to improve stress management."
        ],
        "Low": [
            "Excellent meditation habits — keep it up!",
            "Your regular meditation is helping you stay relaxed."
        ]
    },
    14:{ # working hours column
          "High": [
        "Long working hours can increase stress — try taking short breaks.",
        "Consider balancing work and personal life to reduce stress."
    ],
    "Medium": [
        "Work hours are moderate — maintain a healthy balance."
    ],
    "Low": [
        "Great work-life balance — keep it up!"
    ]
    }
}
     
 