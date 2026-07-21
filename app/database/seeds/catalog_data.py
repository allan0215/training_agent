from __future__ import annotations


# code, display_name, category
EQUIPMENT = [
    ("barbell", "바벨", "free_weight"),
    ("weight_plates", "원판", "free_weight"),
    ("squat_rack", "스쿼트 랙", "rack"),
    ("bench", "플랫 벤치", "bench"),
    ("adjustable_bench", "각도 조절 벤치", "bench"),
    ("dumbbell", "덤벨", "free_weight"),
    ("pullup_bar", "풀업바", "gymnastics"),
    ("rings", "링", "gymnastics"),
    ("climbing_rope", "클라이밍 로프", "gymnastics"),
    ("dip_station", "딥스 바", "gymnastics"),
    ("wall_ball", "월볼", "crossfit"),
    ("plyo_box", "박스", "crossfit"),
    ("cable_machine", "케이블 머신", "machine"),
    ("lat_pulldown_machine", "랫풀다운 머신", "machine"),
    ("leg_curl_machine", "레그 컬 머신", "machine"),
    ("leg_extension_machine", "레그 익스텐션 머신", "machine"),
    ("rower", "로잉머신", "cardio"),
    ("ski_erg", "스키에르그", "cardio"),
    ("assault_bike", "어썰트 바이크", "cardio"),
]


# 각 항목:
# (
#   canonical_name,
#   korean_name,
#   category,
#   default_block_type,
#   extra_aliases,
#   movement_patterns,
#   required_equipment,
# )
#
# movement_patterns:
#   (pattern_code, role, contribution_weight)
EXERCISES = [
    (
        "Back Squat", "백스쿼트", "strength", "resistance",
        ["백 스쿼트", "BS"],
        [("squat", "primary", 1.0), ("core", "stabilizer", 0.3)],
        ["barbell", "weight_plates", "squat_rack"],
    ),
    (
        "Front Squat", "프론트 스쿼트", "strength", "resistance",
        ["프론트스쿼트", "FS"],
        [("squat", "primary", 1.0), ("core", "stabilizer", 0.4)],
        ["barbell", "weight_plates", "squat_rack"],
    ),
    (
        "Deadlift", "데드리프트", "strength", "resistance",
        ["데드", "DL"],
        [("hinge", "primary", 1.0), ("core", "stabilizer", 0.3)],
        ["barbell", "weight_plates"],
    ),
    (
        "Romanian Deadlift", "루마니안 데드리프트", "strength", "resistance",
        ["루마니안 데드", "RDL"],
        [("hinge", "primary", 1.0)],
        ["barbell", "weight_plates"],
    ),
    (
        "Bench Press", "벤치프레스", "strength", "resistance",
        ["벤치", "BP"],
        [("horizontal_push", "primary", 1.0)],
        ["barbell", "weight_plates", "bench", "squat_rack"],
    ),
    (
        "Strict Press", "스트릭트 프레스", "strength", "resistance",
        ["숄더 프레스", "오버헤드 프레스", "OHP"],
        [("vertical_push", "primary", 1.0), ("core", "stabilizer", 0.3)],
        ["barbell", "weight_plates"],
    ),
    (
        "Push Press", "푸시프레스", "strength", "resistance",
        ["푸시 프레스"],
        [("vertical_push", "primary", 1.0), ("squat", "secondary", 0.3)],
        ["barbell", "weight_plates"],
    ),
    (
        "Bent-over Row", "바벨 로우", "strength", "resistance",
        ["벤트오버 로우", "BOR"],
        [("horizontal_pull", "primary", 1.0), ("hinge", "stabilizer", 0.3)],
        ["barbell", "weight_plates"],
    ),
    (
        "Clean", "클린", "weightlifting", "resistance",
        ["스쿼트 클린"],
        [("hinge", "primary", 1.0), ("squat", "secondary", 0.8)],
        ["barbell", "weight_plates"],
    ),
    (
        "Power Clean", "파워클린", "weightlifting", "resistance",
        ["파워 클린", "PC"],
        [("hinge", "primary", 1.0), ("squat", "secondary", 0.4)],
        ["barbell", "weight_plates"],
    ),
    (
        "Clean and Jerk", "클린앤저크", "weightlifting", "resistance",
        ["클린 앤 저크", "C&J"],
        [
            ("hinge", "primary", 1.0),
            ("squat", "secondary", 0.8),
            ("vertical_push", "secondary", 0.8),
        ],
        ["barbell", "weight_plates"],
    ),
    (
        "Snatch", "스내치", "weightlifting", "resistance",
        ["스쿼트 스내치"],
        [
            ("hinge", "primary", 1.0),
            ("squat", "secondary", 0.8),
            ("vertical_push", "stabilizer", 0.4),
        ],
        ["barbell", "weight_plates"],
    ),
    (
        "Power Snatch", "파워스내치", "weightlifting", "resistance",
        ["파워 스내치", "PS"],
        [
            ("hinge", "primary", 1.0),
            ("squat", "secondary", 0.4),
            ("vertical_push", "stabilizer", 0.4),
        ],
        ["barbell", "weight_plates"],
    ),
    (
        "Thruster", "스러스터", "crossfit", "metcon",
        ["쓰러스터"],
        [("squat", "primary", 1.0), ("vertical_push", "primary", 1.0)],
        ["barbell", "weight_plates"],
    ),
    (
        "Pull-up", "풀업", "gymnastics", "skill",
        ["턱걸이", "PU"],
        [("vertical_pull", "primary", 1.0), ("core", "stabilizer", 0.2)],
        ["pullup_bar"],
    ),
    (
        "Chest-to-Bar Pull-up", "체스트투바 풀업", "gymnastics", "skill",
        ["체투바", "C2B"],
        [("vertical_pull", "primary", 1.0), ("core", "stabilizer", 0.3)],
        ["pullup_bar"],
    ),
    (
        "Toes-to-Bar", "토투바", "gymnastics", "skill",
        ["토즈투바", "TTB"],
        [("core", "primary", 1.0), ("vertical_pull", "secondary", 0.4)],
        ["pullup_bar"],
    ),
    (
        "Ring Muscle-up", "링머슬업", "gymnastics", "skill",
        ["링 머슬업", "RMU"],
        [
            ("vertical_pull", "primary", 0.8),
            ("vertical_push", "primary", 0.8),
            ("core", "stabilizer", 0.3),
        ],
        ["rings"],
    ),
    (
        "Bar Muscle-up", "바머슬업", "gymnastics", "skill",
        ["바 머슬업", "BMU"],
        [
            ("vertical_pull", "primary", 0.8),
            ("vertical_push", "primary", 0.8),
            ("core", "stabilizer", 0.3),
        ],
        ["pullup_bar"],
    ),
    (
        "Handstand Push-up", "핸드스탠드 푸시업", "gymnastics", "skill",
        ["핸푸", "HSPU"],
        [("vertical_push", "primary", 1.0), ("core", "stabilizer", 0.3)],
        [],
    ),
    (
        "Handstand Walk", "핸드스탠드 워크", "gymnastics", "skill",
        ["핸드워크", "HSW"],
        [
            ("vertical_push", "stabilizer", 0.5),
            ("core", "primary", 0.7),
            ("locomotion", "primary", 0.7),
        ],
        [],
    ),
    (
        "Rope Climb", "로프클라임", "gymnastics", "skill",
        ["로프 클라임", "RC"],
        [("vertical_pull", "primary", 1.0), ("core", "secondary", 0.4)],
        ["climbing_rope"],
    ),
    (
        "Push-up", "푸시업", "bodyweight", "resistance",
        ["팔굽혀펴기"],
        [("horizontal_push", "primary", 1.0), ("core", "stabilizer", 0.2)],
        [],
    ),
    (
        "Dip", "딥스", "bodyweight", "resistance",
        ["딥"],
        [
            ("vertical_push", "primary", 0.8),
            ("horizontal_push", "secondary", 0.5),
        ],
        ["dip_station"],
    ),
    (
        "Dumbbell Bench Press", "덤벨 벤치프레스", "strength", "resistance",
        ["덤벨 벤치", "DB Bench"],
        [("horizontal_push", "primary", 1.0)],
        ["dumbbell", "bench"],
    ),
    (
        "One-arm Dumbbell Row", "원암 덤벨 로우", "strength", "resistance",
        ["원암 로우", "덤벨 로우"],
        [("horizontal_pull", "primary", 1.0)],
        ["dumbbell"],
    ),
    (
        "Chest Supported Row", "체스트 서포티드 로우", "strength", "resistance",
        ["체스트 서포트 로우"],
        [("horizontal_pull", "primary", 1.0)],
        ["dumbbell", "adjustable_bench"],
    ),
    (
        "Lat Pulldown", "랫풀다운", "strength", "resistance",
        ["랫 풀다운"],
        [("vertical_pull", "primary", 1.0)],
        ["lat_pulldown_machine"],
    ),
    (
        "Seated Cable Row", "시티드 케이블 로우", "strength", "resistance",
        ["케이블 로우"],
        [("horizontal_pull", "primary", 1.0)],
        ["cable_machine"],
    ),
    (
        "Lateral Raise", "레터럴 레이즈", "hypertrophy", "resistance",
        ["사이드 레터럴 레이즈", "사레레"],
        [("other", "primary", 1.0)],
        ["dumbbell"],
    ),
    (
        "Biceps Curl", "바이셉스 컬", "hypertrophy", "resistance",
        ["이두 컬", "덤벨 컬"],
        [("other", "primary", 1.0)],
        ["dumbbell"],
    ),
    (
        "Triceps Pushdown", "트라이셉스 푸시다운", "hypertrophy", "resistance",
        ["삼두 푸시다운", "케이블 푸시다운"],
        [("other", "primary", 1.0)],
        ["cable_machine"],
    ),
    (
        "Leg Curl", "레그 컬", "hypertrophy", "resistance",
        ["라잉 레그 컬"],
        [("knee_flexion", "primary", 1.0)],
        ["leg_curl_machine"],
    ),
    (
        "Leg Extension", "레그 익스텐션", "hypertrophy", "resistance",
        ["레그 익스텐션 머신"],
        [("other", "primary", 1.0)],
        ["leg_extension_machine"],
    ),
    (
        "Burpee", "버피", "crossfit", "metcon",
        ["버피 테스트"],
        [
            ("horizontal_push", "secondary", 0.6),
            ("locomotion", "primary", 0.7),
        ],
        [],
    ),
    (
        "Wall Ball", "월볼", "crossfit", "metcon",
        ["월 볼"],
        [("squat", "primary", 1.0), ("vertical_push", "secondary", 0.6)],
        ["wall_ball"],
    ),
    (
        "Box Jump", "박스 점프", "crossfit", "metcon",
        ["박스점프"],
        [("jump", "primary", 1.0), ("squat", "secondary", 0.4)],
        ["plyo_box"],
    ),
    (
        "Running", "러닝", "cardio", "cardio",
        ["달리기", "Run"],
        [("locomotion", "primary", 1.0)],
        [],
    ),
    (
        "Rowing", "로잉", "cardio", "cardio",
        ["로워", "Row"],
        [
            ("locomotion", "primary", 0.7),
            ("horizontal_pull", "secondary", 0.4),
            ("hinge", "secondary", 0.4),
        ],
        ["rower"],
    ),
    (
        "Ski Erg", "스키에르그", "cardio", "cardio",
        ["스키어그", "Ski"],
        [
            ("locomotion", "primary", 0.6),
            ("vertical_pull", "secondary", 0.4),
            ("hinge", "secondary", 0.3),
        ],
        ["ski_erg"],
    ),
    (
        "Assault Bike", "어썰트 바이크", "cardio", "cardio",
        ["에어바이크", "AB"],
        [("locomotion", "primary", 1.0)],
        ["assault_bike"],
    ),
    (
        "Farmer Carry", "파머 캐리", "strength", "resistance",
        ["파머스 캐리"],
        [("carry", "primary", 1.0), ("core", "stabilizer", 0.5)],
        ["dumbbell"],
    ),
    (
        "Plank", "플랭크", "core", "resistance",
        ["플랭크 홀드"],
        [("core", "primary", 1.0)],
        [],
    ),
    (
        "Hollow Hold", "할로우 홀드", "core", "skill",
        ["할로우 바디 홀드"],
        [("core", "primary", 1.0)],
        [],
    ),
]
