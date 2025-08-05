from django.db import models


class Team(models.Model):
    name = models.CharField(max_length=100)
    leader = models.OneToOneField('Player', on_delete=models.SET_NULL, null=True, blank=True, related_name='leading_team')
    leader_phone = models.CharField(max_length=20)
    reserve_phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.name
    

FACULTY_CHOICES = [
    ("IT", "Informatika texnologiyalari"),
    ("ENG", "Muhandislik"),
    ("MED", "Tibbiyot"),
    # qo‘shish mumkin
]

COURSE_CHOICES = [
    (1, "1-kurs"),
    (2, "2-kurs"),
    (3, "3-kurs"),
    (4, "4-kurs"),
    (5, "5-kurs"),
]

class Player(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="players")
    full_name = models.CharField(max_length=100)
    is_reserve = models.BooleanField(default=False)
    faculty = models.CharField(max_length=50, choices=FACULTY_CHOICES)
    course = models.IntegerField(choices=COURSE_CHOICES)

    def __str__(self):
        return f"{self.full_name} - {self.team.name}"