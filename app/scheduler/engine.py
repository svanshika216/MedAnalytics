import heapq
from datetime import datetime, timedelta
from app.models import Appointment, DoctorAvailability

class AppointmentScheduler:
    PRIORITY_MAP = {
        'emergency' : 1,
        'urgent' : 2,
        'normal' : 3
    }

    def __init__(self):
        self._heap = []

    def push(self, appointment):
        priority_int = self.PRIORITY_MAP.get(appointment.priority, 3)
        heapq.heappush(self._heap, (
            priority_int,
            appointment.created_at,
            appointment.id
        ))

    def pop(self):
        if self._heap:
            return heapq.heappop(self._heap)
        return None

    def peek(self):
        if self._heap:
            return self._heap[0]
        return None
    
    def size(self):
        return len(self._heap)
    
    @staticmethod
    def check_doctor_available(doctor, requested_time):
        day_name = requested_time.strftime('%A')
        requested_time_only = requested_time.time()

        for slot in doctor.availability:
            if slot.day_of_week == day_name:
                if slot.start_time <= requested_time_only <= slot.end_time:
                    return True
        return False

    @staticmethod
    def check_slot_conflict(doctor_id, requested_time, exclude_appointment_id=None):
            window_start = requested_time - timedelta(minutes=30)
            window_end = requested_time + timedelta(minutes=30)

            query = Appointment.query.filter(
                Appointment.doctor_id == doctor_id,
                Appointment.scheduled_time >= window_start,
                Appointment.scheduled_time <= window_end,
                Appointment.status != 'cancelled'
            )

            if exclude_appointment_id:
                query = query.filter(Appointment.id != exclude_appointment_id)

            return query.first() is not None
    

    @staticmethod
    def suggest_next_slot(doctor, requested_time):
        day_name = requested_time.strftime('%A')

        for slot in doctor.availability:
            if slot.day_of_week == day_name:
                candidate = requested_time.replace(
                    hour=slot.start_time.hour,
                    minute=slot.start_time.minute,
                    second=0,
                    microsecond=0
                )

                slot_end = requested_time.replace(
                    hour=slot.end_time.hour,
                    minute=slot.end_time.minute,
                    second=0,
                    microsecond=0
                )

                while candidate <= slot_end:
                    conflict = AppointmentScheduler.check_slot_conflict(
                        doctor.id, candidate
                    )
                    if not conflict:
                        return candidate
                    candidate += timedelta(minutes=30)

        return None
    
scheduler = AppointmentScheduler()
            
