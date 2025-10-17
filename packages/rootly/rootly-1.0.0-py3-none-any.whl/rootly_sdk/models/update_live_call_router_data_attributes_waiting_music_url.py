from enum import Enum


class UpdateLiveCallRouterDataAttributesWaitingMusicUrl(str, Enum):
    HTTPSSTORAGE_ROOTLY_COMTWILIOVOICEMAILBUSYSTRINGS_MP3 = (
        "https://storage.rootly.com/twilio/voicemail/BusyStrings.mp3"
    )
    HTTPSSTORAGE_ROOTLY_COMTWILIOVOICEMAILCLOCKWORKWALTZ_MP3 = (
        "https://storage.rootly.com/twilio/voicemail/ClockworkWaltz.mp3"
    )
    HTTPSSTORAGE_ROOTLY_COMTWILIOVOICEMAILITH_BRAHMS_116_4_MP3 = (
        "https://storage.rootly.com/twilio/voicemail/ith_brahms-116-4.mp3"
    )
    HTTPSSTORAGE_ROOTLY_COMTWILIOVOICEMAILITH_CHOPIN_15_2_MP3 = (
        "https://storage.rootly.com/twilio/voicemail/ith_chopin-15-2.mp3"
    )
    HTTPSSTORAGE_ROOTLY_COMTWILIOVOICEMAILMARKOVICHAMP_BORGHESTRAL_MP3 = (
        "https://storage.rootly.com/twilio/voicemail/MARKOVICHAMP-Borghestral.mp3"
    )
    HTTPSSTORAGE_ROOTLY_COMTWILIOVOICEMAILMELLOTRONIAC_FLIGHT_OF_YOUNG_HEARTS_FLUTE_MP3 = (
        "https://storage.rootly.com/twilio/voicemail/Mellotroniac_-_Flight_Of_Young_Hearts_Flute.mp3"
    )
    HTTPSSTORAGE_ROOTLY_COMTWILIOVOICEMAILOLDDOG_ENDLESS_GOODBYE_28INSTR_29_MP3 = (
        "https://storage.rootly.com/twilio/voicemail/oldDog_-_endless_goodbye_%28instr.%29.mp3"
    )

    def __str__(self) -> str:
        return str(self.value)
