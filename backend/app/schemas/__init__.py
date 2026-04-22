from app.schemas.auth import *
from app.schemas.curriculum import *
from app.schemas.student import *
from app.schemas.teacher import *
from app.schemas.leaderboard import *
from app.schemas.classes import *
from app.schemas.assignment import *

# Explicitly export new schemas
from app.schemas.student import StreakResponse, StatsResponse
from app.schemas.curriculum import LessonResponse, LessonDetailResponse
