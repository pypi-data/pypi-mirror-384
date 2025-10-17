from enum import Enum


class Gender(Enum):
    MALE = "Male"
    FEMALE = "Female"


class EducationForm(Enum):
    FULL_TIME = "FullTime"
    PART_TIME = "PartTime"
    EXTRAMURAL = "Extramural"


class EducationBasise(Enum):
    NATURAL_PERSON = "NaturalPerson"
    LEGAL_PERSON = "LegalPerson"
    NATURAL_AND_LEGAL_PERSON = "NaturalAndLegalPerson"
    FEDERAL_BUDGET = "FederalBudget"
    FEDERAL_BUDGET_CONTRACT = "FederalBudgetContract"
    FEDERAL_BUDGET_MILITARY_CONTRACT = "FederalBudgetMilitaryContract"
    RF_SUBJECT_BUDGET = "RfSubjectBudget"
    RF_SUBJECT_BUDGET_CONTRACT = "RfSubjectBudgetContract"
    LOCAL_BUDGET = "LocalBudget"
    LOCAL_BUDGET_CONTRACT = "LocalBudgetContract"
    NATURAL_AND_LEGAL_PERSON_CONTRACT = "NaturalAndLegalPersonContract"
    EDUCATION_CERTIFICATE = "EducationCertificate"


class EducationDepth(Enum):
    BASE = "Base"
    IN_DEPTH = "InDepth"


class BaseEducationLevel(Enum):
    BASIS_GENERAL = "BasisGeneral"
    GENERAL_SECONDARY = "GeneralSecondary"
    SECONDARY_PROFESSIONAL = "SecondaryProfessional"
    WITHOUT_BASIC_GENERAL = "WithoutBasicGeneral"


class EducationLevel(Enum):
    BASIC = "Basic"
    SECONDARY = "Secondary"
    VOCATIONAL_BASIC = "VocationalBasic"
    VOCATIONAL_SECONDARY = "VocationalSecondary"
    INCOMPLETE_SECONDARY = "IncompleteSecondary"
    HIGHER_BACHELOR = "HigherBachelor"
    HIGHER_MAGISTRACY = "HigherMagistracy"
    HIGHER_POST_GRADUATE = "HigherPostGraduate"
    HIGHER_INCOMPLETE = "HigherIncomplete"
    WITHOUT_BASIC = "WithoutBasic"
    BEGINING_PROFESSIONAL = "BeginingProfessional"
    SECONDARY_PROFESSIONAL = "SecondaryProfessional"


class TermType(Enum):
    SEMESTER = "Semester"
    TRIMESTER = "Trimester"
    COURSE = "Course"

    def to_value(self):
        return {
            TermType.SEMESTER: "Семестр",
            TermType.TRIMESTER: "Триместр",
            TermType.COURSE: "Курс",
        }[self]


class ExaminationStage(Enum):
    TUTORIAL = "Tutorial"
    EXAMINATION = "Examination"
    RETAKE = "Retake"


class CertificationType(Enum):
    PRE_GRADUATION_PRACTICE = "PreGraduationPractice"
    GRADUATION_WORK = "GraduationWork"
    STATE_EXAM = "StateExam"


class ThematicPlanLessonType(Enum):
    LECTURE = "Lecture"
    PRACTICE = "Practice"
    LABORATORY = "Laboratory"
    SELF = "Self"
    LESSON = "Lesson"
    CONSULTATION = "Consultation"
    SEMINAR = "Seminar"
    EXCURSION = "Excursion"
    EXAMINATION = "Examination"
    COMPOSITION = "Composition"
    BUSINESS_GAME = "BusinessGame"
    PRACTICAL_TRAINING = "PracticalTraining"
    SPORT_STANDARTS = "SportStandarts"
    PRACTICAL_WORK = "PracticalWork"


class RelationshipType(Enum):
    MOTHER = "Mother"
    FATHER = "Father"
    RELATIVE = "Relative"
    ADOPTIVE_PARENT = "AdoptiveParent"
    STEPPARENT = "Stepparent"
    GUARDIAN = "Guardian"
    TRUSTEE = "Trustee"


class LegalStatu(Enum):
    AUTONOMOUS = "Autonomous"
    STATE_FINANCED = "StateFinanced"
    STATE_OWNED = "StateOwned"
    PRIVATE_OWNED = "PrivateOwned"


class ClassroomType(Enum):
    CABINET = "Cabinet"
    LABORATORY = "Laboratory"
    HALL = "Hall"
    MULTIMEDIA_CABINET = "MultimediaCabinet"
    COMPUTER_CLASS = "ComputerClass"
    WORKROOM = "Workroom"
    STUDIO = "Studio"
    SPORTS_COMPLEX = "SportsComplex"
    FIRING_FIELD = "FiringField"
    FITNESS_COMPLEX = "FitnessComplex"
    TRAINING_WORKSHOP = "TrainingWorkshop"


class ExaminationType(Enum):
    EXAM = "Exam"
    DIFFERENTIATED_TEST = "DifferentiatedTest"
    TEST = "Test"
    OTHER = "Other"
    PROFESSIONAL_MODULE = "ProfessionalModule"
    COURSE_WORK = "CourseWork"


class GradingSystem(Enum):
    BY_MARKS = "ByMarks"
    BY_PASS_FAIL = "ByPassFail"


class SubjectType(Enum):
    REGULAR = "Regular"
    PRACTICAL_TRAINING = "PracticalTraining"
    INTERNSHIP = "Internship"
    MDK = "Mdk"


class EducationPlanSectionType(Enum):
    REGULAR = "Regular"
    PROFESSIONAL_MODULE = "ProfessionalModule"


class EducationTaskType(Enum):
    LESSON = "Lesson"
    CONTROL = "Control"
    INDEPENDENT = "Independent"
    LABORATORY = "Laboratory"
    SLICE = "Slice"
    HOME = "Home"
    REVIEW = "Review"
    TEST = "Test"
    REPORT = "Report"
    COLLOQUIUM = "Colloquium"
    SPORT_STANDARTS = "SportStandarts"
    PRACTICAL_WORK = "PracticalWork"


class DecreeType(Enum):
    HIRE = "Hire"
    FIRE = "Fire"
    APPOINT = "Appoint"
    DISMISS = "Dismiss"
    ENROLL = "Enroll"
    RETIRE = "Retire"
    MOVE = "Move"
    NEXT_TERM = "NextTerm"
    NEXT_YEAR = "NextYear"
    GRADUATE = "Graduate"
    DISBAND = "Disband"


class EnrollmentReason(Enum):
    FREE_ENROLLMENT = "FreeEnrollment"
    FREE_ENROLLMENT_FAST = "FreeEnrollmentFast"
    UNIFIED_STATE_EXAM = "UnifiedStateExam"
    UNIFIED_STATE_EXAM_AND_ADDITIONAL_EXAMS = "UnifiedStateExamAndAdditionalExams"
    ORGANIZATION_EXAMS = "OrganizationExams"
    FINAL_EXAMS = "FinalExams"
    OTHER_EDUCATION_FORM = "OtherEducationForm"
    OTHER_EDUCATION_ORGANIZATIONS = "OtherEducationOrganizations"
    BACK_FROM_PREV_EXPELLED = "BackFromPrevExpelled"
    BACK_FROM_ARMY = "BackFromArmy"
    OTHER_REASONS = "OtherReasons"
    AVERAGE_ATTESTATION_POINT = "AverageAttestationPoint"
    AVERAGE_ATTESTATION_POINT_AND_ADDITIONAL_EXAMS = (
        "AverageAttestationPointAndAdditionalExams"
    )
    BACK_FROM_ACADEMIC_VACATION = "BackFromAcademicVacation"


class RetirementReason(Enum):
    TRANSFER_ON_OTHER_EDUCATION_FORM_IN_THIS_ORGANIZATION = (
        "TransferOnOtherEducationFormInThisOrganization"
    )
    TRANSFER_IN_OTHER_EDUCATION_ORGANIZATIONS = "TransferInOtherEducationOrganizations"
    DISEASE = "Disease"
    PERSONAL_DESIRE = "PersonalDesire"
    SEND_DOWN = "SendDown"
    SEND_DOWN_FOR_POOR_PROGRESS = "SendDownForPoorProgress"
    SEND_DOWN_FOR_FAIL_FINAL_EXAMS = "SendDownForFailFinalExams"
    CONSCRIPTION = "Conscription"
    OTHER_REASONS = "OtherReasons"
    GRADUATION = "Graduation"
    TERMINATION_OF_CONTRACT = "TerminationOfContract"
    STUDENTS_DEATH = "StudentsDeath"
    ACADEMIC_VACATION = "AcademicVacation"
    NO_PAYMENT = "NoPayment"
    ORGANIZATION_LIQUIDATION = "OrganizationLiquidation"
    ILLEGAL_ENROLLMENT = "IllegalEnrollment"
    COURT_SENTENCE = "CourtSentence"
    AS_DISCIPLINARY_MEASURE = "AsDisciplinaryMeasure"


class RetirementReasonsWithoutGraduation(Enum):
    TRANSFER_ON_OTHER_EDUCATION_FORM_IN_THIS_ORGANIZATION = (
        "TransferOnOtherEducationFormInThisOrganization"
    )
    TRANSFER_IN_OTHER_EDUCATION_ORGANIZATIONS = "TransferInOtherEducationOrganizations"
    DISEASE = "Disease"
    PERSONAL_DESIRE = "PersonalDesire"
    SEND_DOWN = "SendDown"
    SEND_DOWN_FOR_POOR_PROGRESS = "SendDownForPoorProgress"
    SEND_DOWN_FOR_FAIL_FINAL_EXAMS = "SendDownForFailFinalExams"
    CONSCRIPTION = "Conscription"
    OTHER_REASONS = "OtherReasons"
    TERMINATION_OF_CONTRACT = "TerminationOfContract"
    STUDENTS_DEATH = "StudentsDeath"
    ACADEMIC_VACATION = "AcademicVacation"
    NO_PAYMENT = "NoPayment"
    ORGANIZATION_LIQUIDATION = "OrganizationLiquidation"
    ILLEGAL_ENROLLMENT = "IllegalEnrollment"
    COURT_SENTENCE = "CourtSentence"
    AS_DISCIPLINARY_MEASURE = "AsDisciplinaryMeasure"


class MarkRating(Enum):
    FAIL = "Fail"
    SUCCESS = "Success"
    TWO = "Two"
    THREE = "Three"
    FOUR = "Four"
    FIVE = "Five"

    def to_value(self):
        return {
            MarkRating.TWO: "2",
            MarkRating.THREE: "3",
            MarkRating.FOUR: "4",
            MarkRating.FIVE: "5",
            MarkRating.SUCCESS: "зачёт",
            MarkRating.FAIL: "незачет",
        }[self]


class AbsenceType(Enum):
    IS_LATE = "IsLate"
    IS_ABSENT_BY_VALID_REASON = "IsAbsentByValidReason"
    IS_ABSENT_BY_NOT_VALID_REASON = "IsAbsentByNotValidReason"
    SICK_LEAVE = "SickLeave"

    def to_value(self):
        return {
            AbsenceType.IS_ABSENT_BY_NOT_VALID_REASON: "нп",
            AbsenceType.IS_ABSENT_BY_VALID_REASON: "уп",
            AbsenceType.IS_LATE: "оп",
            AbsenceType.SICK_LEAVE: "б",
        }[self]


class MilitaryRank(Enum):
    CONSCRIPT = "Conscript"
    COMMON_SOLDIER = "CommonSoldier"
    LANCE_CORPORAL = "LanceCorporal"
    LANCE_SERGEANT = "LanceSergeant"
    SERGEANT = "Sergeant"
    STAFF_SERGEANT = "StaffSergeant"
    PETTY_OFFICER = "PettyOfficer"
    ENSIGN = "Ensign"
    SENIOR_ENSIGN = "SeniorEnsign"
    SUBLIEUTENANT = "Sublieutenant"
    LIEUTENANT = "Lieutenant"
    SENIOR_LIEUTENANT = "SeniorLieutenant"
    CAPTAIN = "Captain"
    MAJOR = "Major"
    LIEUTENANT_COLONEL = "LieutenantColonel"
    COLONEL = "Colonel"
    MAJOR_GENERAL = "MajorGeneral"
    LIEUTENANT_GENERAL = "LieutenantGeneral"
    COLONEL_GENERAL = "ColonelGeneral"
    GENERAL_OF_THE_ARMY = "GeneralOfTheArmy"
    MARSHAL = "Marshal"


class MilitaryComposition(Enum):
    SOLDIERS_AND_SAILORS = "SoldiersAndSailors"
    ENSIGN_AND_WARRANT_OFFICERS = "EnsignAndWarrantOfficers"
    OFFICERS_AND_MARSHALS = "OfficersAndMarshals"


class FitnessForMilitaryService(Enum):
    FIT = "Fit"
    FIT_WITH_SMALL_LIMITATIONS = "FitWithSmallLimitations"
    LIMITEDLY_FIT = "LimitedlyFit"
    TEMPORARILY_UNFIT = "TemporarilyUnfit"
    UNFIT = "Unfit"


class ReserveCategorie(Enum):
    FIRST_CATEGORY = "FirstCategory"
    SECOND_CATEGORY = "SecondCategory"


class GroupsOfAccounting(Enum):
    ARMY = "Army"
    FLEET = "Fleet"


class EducationProgramType(Enum):
    VOCATIONAL_BASIC = "VocationalBasic"
    VOCATIONAL_BASIC_EXECUTIVES = "VocationalBasicExecutives"
    VOCATIONAL_SECONDARY = "VocationalSecondary"
    VOCATIONAL_SECONDARY_TRAINING = "VocationalSecondaryTraining"
    VOCATIONAL_SECONDARY_RETRAINING = "VocationalSecondaryRetraining"
    VOCATIONAL_ADDITIONAL = "VocationalAdditional"


class SpecialtyType(Enum):
    VOCATIONAL_BASIC = "VocationalBasic"
    VOCATIONAL_BASIC_EXECUTIVES = "VocationalBasicExecutives"
    VOCATIONAL_SECONDARY = "VocationalSecondary"
    VOCATIONAL_SECONDARY_TRAINING = "VocationalSecondaryTraining"
    VOCATIONAL_SECONDARY_RETRAINING = "VocationalSecondaryRetraining"
    VOCATIONAL_ADDITIONAL = "VocationalAdditional"


class PositionType(Enum):
    EXECUTIVES = "Executives"
    TEACHING_STAFF = "TeachingStuff"
    SUPPORT_STUFF = "SupportStuff"
    SERVICE_STUFF = "ServiceStuff"


class AcademicDegree(Enum):
    DOCTORATE = "Doctorate"
    DOCTORANT = "Doctorant"


class AcademicTitle(Enum):
    PROFESSOR = "Professor"
    ASSOCIATE_PROFESSOR = "AssociateProfessor"


class LaborContract(Enum):
    EMPLOYMENT = "Employment"
    PART_TIME = "PartTime"
    WORK = "Work"


class QualificationCategorie(Enum):
    NONE = "None"
    CONFORMITY = "Conformity"
    HIGHER = "Higher"
    FIRST = "First"


class DisabilityGroup(Enum):
    FIRST = "First"
    SECOND = "Second"
    THIRD = "Third"
    DISABLED_CHILD = "DisabledChild"


class HealthCategorie(Enum):
    HEARING_LOSS = "HearingLoss"
    SIGHT_DISORDERS = "SightDisorders"
    SPEECH_DISORDERS = "SpeechDisorders"
    MUSCULOSKELETAL_DISORDERS = "MusculoskeletalDisorders"
    MENTAL_DISORDERS = "MentalDisorders"
    INTELLECTUAL_DISABILITY = "IntellectualDisability"
    AUTISM = "Autism"
    COMPLEX_DEFECTS = "ComplexDefects"
    SOMATIC_DEFECTS = "SomaticDefects"


class LearningLanguage(Enum):
    ENGLISH = "English"
    FRENCH = "French"
    GERMAN = "German"


class OrganizationStatu(Enum):
    FUNCTION = "Function"
    OVERHAUL = "Overhaul"
    RECONSTRUCTION = "Reconstruction"
    ACTIVITIES_SUSPENDED = "ActivitiesSuspended"
    CONTINGENT_MISSING = "ContingentMissing"
    AWAITING_OPENING = "AwaitingOpening"
    LIQUIDATED = "Liquidated"
    CLOSED = "Closed"
    JOIN_TO_OTHER_ORG = "JoinToOtherOrg"


class PortfolioType(Enum):
    ACTIVITY = "Activity"
    PROJECT = "Project"
    OUTCLASS_ACTIVITY = "OutclassActivity"
    OUTCLASS_ORGANIZATIONAL = "OutclassOrganizational"
    OUTCLASS_NON_EDUCATIONAL = "OutclassNonEducational"
    OUTCLASS_INDIVIDUAL = "OutclassIndividual"


class EventType(Enum):
    OTHER = "Other"
    OLYMPICS = "Olympics"
    CONTEST = "Contest"
    SHOW = "Show"
    CHAMPIONSHIP_YAMALSKILLS = "ChampionshipYamalskills"


class InvolvementDegree(Enum):
    OTHER = "Other"
    FAMILIARIZATION = "Familiarization"
    PRE_GRADUATION_PROJECT = "PreGraduationProject"
    IMPL_OWN_PROJECT = "ImplOwnProject"


class ParticipantStatuse(Enum):
    WINNER = "Winner"
    AWARDEE = "Awardee"
    PARTICIPANT = "Participant"


class EventStatuse(Enum):
    OTHER = "Other"
    INTERNATIONAL = "International"
    COUNTRY = "Country"
    INTER_REGION = "InterRegion"
    REGION = "Region"
    INTER_DISTRICT = "InterDistrict"
    DISTRICT = "District"
    CITY = "City"
    INTER_ORGANIZATION = "InterOrganization"
    ORGANIZATION = "Organization"


class InstitutionOrganizationType(Enum):
    POO = "Poo"
    DPO = "Dpo"


class EducationDocumentType(Enum):
    CERTIFICATE_SECONDARY = "CertificateSecondary"
    CERTIFICATE_BASIC = "CertificateBasic"
    DIPLOMA_PROF = "DiplomaProf"
    DIPLOMA_BARCHELOR = "DiplomaBarchelor"
    DIPLOMA_SPECIALIST = "DiplomaSpecialist"
    DIPLOMA_MASTER = "DiplomaMaster"
    DIPLOMA_POSTGRADUATE = "DiplomaPostgraduate"
    DIPLOMA_RESIDENCY = "DiplomaResidency"
    DIPLOMA_ASSISTANTSHIP = "DiplomaAssistantship"
    CERTIFICATE_PROF_DEVELOPMENT = "CertificateProfDevelopment"
    DIPLOMA_PROF_RETRAIN = "DiplomaProfRetrain"
    CERTIFICATE_WORKER = "CertificateWorker"
    CERTIFICATE_DISABILITY_TRAIN = "CertificateDisabilityTrain"
    CERTIFICATE_ART = "CertificateArt"
    DOCUMENT_OTHER_EDUC = "DocumentOtherEduc"
    DOCUMENT_OTHER_TRAIN = "DocumentOtherTrain"
    TRAINING_CERTIFICATE = "TrainingCertificate"
    ACADEMIC_CERTIFICATE = "AcademicCertificate"
    DIPLOMA_PROF_BASIC = "DiplomaProfBasic"
    DIPLOMA_PROF_UPPER = "DiplomaProfUpper"
    DIPLOMA_PROF_HONORS_BASIC = "DiplomaProfHonorsBasic"
    DIPLOMA_PROF_HONORS_UPPER = "DiplomaProfHonorsUpper"
    DIPLOMA_PROF_HONORS = "DiplomaProfHonors"
    DIPLOMA_PROF_PRIMARY = "DiplomaProfPrimary"
    DIPLOMA_PROF_PRIMARY_GOLDEN_MEDAL = "DiplomaProfPrimaryGoldenMedal"
    DIPLOMA_PROF_PRIMARY_SILVER_MEDAL = "DiplomaProfPrimarySilverMedal"
    DIPLOMA_PROF_PRIMARY_HONORS = "DiplomaProfPrimaryHonors"


class ProfDocType(Enum):
    DIPLOMA = "Diploma"
    CERTIFICATE_POSTGRADUATE = "CertificatePostgraduate"
    CERTIFICATION_OF_PASSED_EXAMS = "CertificationOfPassedExams"


class FileDataCategorie(Enum):
    REQUEST_CERTIFICATION = "RequestCertification"
    PREV_CERT_COPY = "PrevCertCopy"
    SECTION1 = "Section1"
    SECTION2 = "Section2"
    SECTION3 = "Section3"
    SECTION4 = "Section4"
    AGREEMENT_OF_PROCESSING_PERSONAL_DATA = "AgreementOfProcessingPersonalData"


class PortfolioDocumentType(Enum):
    EDUCATION = "Education"
    REFRESHER_COURSE = "RefresherCourse"
    PROF_DEVELOPMENT = "ProfDevelopment"
    SECOND_HIGHER = "SecondHigher"
    SCIENTIFIC_AND_METHODOLOGICAL = "ScientificAndMethodological"


class ScienceEventStatuse(Enum):
    MUNICIPAL = "Municipal"
    REGIONAL = "Regional"
    FEDERAL = "Federal"
    INTERNATIONAL = "International"


class ParticipationStatuse(Enum):
    OTHER = "Other"
    AUTHOR = "Author"
    COAUTHOR = "Coauthor"


class RequestStatuse(Enum):
    DRAFT = "Draft"
    REGISTERED = "Registered"
    APPROVED = "Approved"
    REFUSED = "Refused"
    PORTFOLIO_CONFIRMATION = "PortfolioConfirmation"
    DATA_CONFIRMED = "DataConfirmed"
    EXPERTISE = "Expertise"
    PORTFOLIO_CORRECTING = "PortfolioCorrecting"
    EXPERTISE_COMPLETE = "ExpertiseComplete"
    EXPERTISE_ACCEPTED = "ExpertiseAccepted"
    EXPERTISE_RETURNED = "ExpertiseReturned"
    GAK_MEETING = "GakMeeting"
    CATEGORY_ASSIGNED = "CategoryAssigned"
    CATEGORY_REFUSED = "CategoryRefused"
    WITHDRAWN = "Withdrawn"


class PositionKind(Enum):
    MAIN = "Main"
    ADDITIONAL = "Additional"


class ProfDocumentType(Enum):
    DIPLOMA = "Diploma"
    CERTIFICATE_POSTGRADUATE = "CertificatePostgraduate"
    CERTIFICATION_OF_PASSED_EXAMS = "CertificationOfPassedExams"


class EducationKind(Enum):
    SECOND_PROF_EDUCATION = "SecondProfEducation"
    PROF_RETRAINING = "ProfRetraining"
    INTERNSHIP = "Internship"


class DisabilityCategorie(Enum):
    CHILDHOOD = "Childhood"
    TRAUMA = "Trauma"
    WAR_INJURES = "WarInjuries"


class PhysicalGroup(Enum):
    BASIC = "Basic"
    PREPARATORY = "Preparatory"
    EXEMPT = "Exempt"
    LFK = "Lfk"
    SPECIAL = "Special"


class IdentityDocumentType(Enum):
    OTHER = "Other"
    BIRTH_CERTIFICATE = "BirthCertificate"
    RF_PASSPORT = "RfPassport"
    INTERNATIONAL_RF_PASSPORT = "InternationalRfPassport"
    OFFICER_ID = "OfficerId"
    MILITARY_ID = "MilitaryId"
    TEMPORARY_MILITARY_ID = "TemporaryMilitaryId"
    TEMPORARY_ID = "TemporaryId"
    FOREIGN_PASSPORT = "ForeignPassport"
    ID_WITHOUTCITIZENSHIP = "IdWithoutcitizenship"
    ID_CERTAIN_CATEGORIES = "IdCertainCategories"
    REFUGEE_ID = "RefugeeId"
    RESIDENCE_PERMIT = "ResidencePermit"
    TEMPORARY_RESIDENCE_PERMIT = "TemporaryResidencePermit"
    CERTIFICATE_OF_REFUGEE_PETITION = "CertificateOfRefugeePetition"
    CERTIFICATE_OF_TEMPORARY_ASYLUM = "CertificateOfTemporaryAsylum"
    FOREIGN_BIRTH_CERTIFICATE = "ForeignBirthCertificate"


class ForeignIdentityDocumentType(Enum):
    OTHER = "Other"
    BIRTH_CERTIFICATE = "BirthCertificate"
    RF_PASSPORT = "RfPassport"


class NeedInHostelType(Enum):
    NOT_NEEDED = "NotNeeded"
    NEEDED = "Needed"
    LIVE = "Live"


class ExaminationItemType(Enum):
    SCHEDULE_SUBJECT = "ScheduleSubject"
    PROF_MODULE = "ProfModule"
    LIVE = "Live"


class AuditType(Enum):
    INSERT = "1"
    UPDATE = "2"
    DELETE = "4"
    LOG_IN = "8"
    LOGIN_ESIA = "16"
    LOG_OUT = "32"


class AuditSection(Enum):
    CERTIFICATION_MARK = "CertificationMark"
    PROFESSIONAL_MODULE = "ProfessionalModule"
    DECREE = "Decree"
    ATTESTATION = "Attestation"
    LESSON = "Lesson"
    COURSEWORK = "Coursework"
    AUTHENTICATION = "Authentication"
    USER_PROFILE = "UserProfile"
    SUPPLEMENTARY_EDUCATION_CERTIFICATE = "SupplementaryEducationCertificate"


class ActionType(Enum):
    INSERT = "Insert"
    UPDATE = "Update"
    DELETE = "Delete"
    LOG_IN = "LogIn"
    LOGIN_ESIA = "LoginEsia"
    LOG_OUT = "LogOut"


class CertificateStatuse(Enum):
    FROZEN = "Frozen"
    ACTIVATED = "Activated"
    NOT_ACTIVATED = "NotActivated"


class CertificateActualitie(Enum):
    NOT_ACTUAL = "NotActual"
    ACTUAL = "Actual"
    WAITING = "Waiting"


class CertificateScreenState(Enum):
    NOT_ALLOWED = "1"
    NOT_AVAILABLE = "2"
    AVAILABLE = "3"
    ONLY_PARENT = "4"


class FactHoursViewType(Enum):
    BY_SUBJECT = "1"
    BY_PERIOD = "2"


class UserPreferencePage(Enum):
    STUDENT_LIST = "StudentList"
    EMPLOYEE_LIST = "EmployeeList"
    RETIRED_STUDENT_LIST = "RetiredStudentList"
    EXPELLED_STUDENT_LIST = "ExpelledStudentList"
    ENROLLEE_LIST = "EnrolleeList"
    PARENT_LIST = "ParentList"


class UserPreferenceSetting(Enum):
    ITEM_COUNT_ON_PAGE = "ItemCountOnPage"


class StudentType(Enum):
    STUDENT = "Student"
    EXPELLED = "Expelled"
    RETIRED = "Retired"


class PlaceOfDemand(Enum):
    MILITARY_COMMISSARIAT = "MilitaryCommissariat"
    ANOTHER = "Another"
    PENSION_FUND = "PensionFund"


class ChatType(Enum):
    TEACHER_CHAT = "TeacherChat"
    EMPLOYEE_CHAT = "EmployeeChat"
    GROUP_CHAT = "GroupChat"
    PARENT_CHAT = "ParentChat"
    SUBJECT_CHAT = "SubjectChat"


class FormsOfTraining(Enum):
    IN_EDUCATION_ORGANIZATION = "InEducationOrganization"
    OUT_OF_EDUCATION_ORGANIZATION = "OutOfEducationOrganization"


class EducationDocumentStatuse(Enum):
    ORIGINAL = "Original"
    DUPLICATE = "Duplicate"


class RFSubject(Enum):
    ALTAY_REGION = "AltayRegion"
    AMUR_REGION = "AmurRegion"
    ARHANGELSK_REGION = "ArhangelskRegion"
    ASTRAKHAN_REGION = "AstrakhanRegion"
    BELGOROD_REGION = "BelgorodRegion"
    BRYANSK_REGION = "BryanskRegion"
    VLADIMIR_REGION = "VladimirRegion"
    VOLGOGRAD_REGION = "VolgogradRegion"
    VOLOGDA_REGION = "VologdaRegion"
    VORONEZH_REGION = "VoronezhRegion"
    MOSCOW = "Moscow"
    JEWISH_AUTONOMOUS_REGION = "JewishAutonomousRegion"
    TRANSBAIKAL_REGION = "TransbaikalRegion"
    IVANOVO_REGION = "IvanovoRegion"
    IRKUTSK_REGION = "IrkutskRegion"
    KABARDINO_BALKARIAN_REGION = "KabardinoBalkarianRegion"
    KALININGRAD_REGION = "KaliningradRegion"
    KALUGA_REGION = "KalugaRegion"
    KAMCHATKA_KRAI = "KamchatkaKrai"
    KARACHAY_CHERKESS_REPUBLIC = "KarachayCherkessRepublic"
    KEMEROVO_REGION = "KemerovoRegion"
    KIROV_REGION = "KirovRegion"
    KOSTROMA_REGION = "KostromaRegion"
    KRASNODAR_REGION = "KrasnodarRegion"
    KRASNOYARSK_REGION = "KrasnoyarskRegion"
    KURGAN_REGION = "KurganRegion"
    KURSK_REGION = "KurskRegion"
    LENINGRAD_REGION = "LeningradRegion"
    LIPETSK_REGION = "LipetskRegion"
    MAGADAN_REGION = "MagadanRegion"
    MOSCOW_REGION = "MoscowRegion"
    MURMANSK_REGION = "MurmanskRegion"
    NENETS_AUTONOMOUS_OKRUG = "NenetsAutonomousOkrug"
    NIZHNY_NOVGOROD_REGION = "NizhnyNovgorodRegion"
    NOVGOROD_REGION = "NovgorodRegion"
    NOVOSIBIRSK_REGION = "NovosibirskRegion"
    OMSK_REGION = "OmskRegion"
    ORENBURG_REGION = "OrenburgRegion"
    ORYOL_REGION = "OryolRegion"
    PENZA_REGION = "PenzaRegion"
    PERM_REGION = "PermRegion"
    PRIMORSKY_KRAI = "primorskyKrai"
    PSKOV_REGION = "PskovRegion"
    REPUBLIC_OF_ADYGEA = "RepublicOfAdygea"
    ALTAI_REPUBLIC = "AltaiRepublic"
    REPUBLIC_OF_BASHKORTOSTAN = "RepublicOfBashkortostan"
    REPUBLIC_OF_BURYATIA = "RepublicOfBuryatia"
    REPUBLIC_OF_DAGESTAN = "RepublicOfDagestan"
    REPUBLIC_OF_INGUSHETIA = "RepublicOfIngushetia"
    REPUBLIC_OF_KALMYKIA = "RepublicOfKalmykia"
    REPUBLIC_OF_KARELIA = "RepublicOfKarelia"
    KOMI_REPUBLIC = "KomiRepublic"
    REPUBLIC_OF_CRIMEA = "RepublicOfCrimea"
    REPUBLIC_OF_MARI_EL = "RepublicOfMariEl"
    REPUBLIC_OF_MORDOVIA = "RepublicOfMordovia"
    REPUBLIC_OF_SAKHA = "RepublicOfSakha"
    REPUBLIC_OF_NORTH_OSSETIA_ALANIA = "RepublicOfNorthOssetiaAlania"
    REPUBLIC_OF_TATARSTAN = "RepublicOfTatarstan"
    REPUBLIC_OF_TYVA = "RepublicOfTyva"
    REPUBLIC_OF_KHAKASSIA = "RepublicOfKhakassia"
    ROSTOV_REGION = "RostovRegion"
    RYAZAN_REGION = "RyazanRegion"
    SAMARA_REGION = "SamaraRegion"
    SAINT_PETERSBURG = "SaintPetersburg"
    SARATOV_REGION = "SaratovRegion"
    SAKHALIN_REGION = "SakhalinRegion"
    SVERDLOVSK_REGION = "SverdlovskRegion"
    SEVASTOPOL = "Sevastopol"
    SMOLENSK_REGION = "SmolenskRegion"
    STAVROPOL_REGION = "StavropolRegion"
    TAMBOV_REGION = "TambovRegion"
    TVER_REGION = "TverRegion"
    TOMSK_REGION = "TomskRegion"
    TULA_REGION = "TulaRegion"
    TYUMEN_REGION = "TyumenRegion"
    UDMURTКEPUBLIC = "UdmurtКepublic"
    ULYANOVSK_REGION = "UlyanovskRegion"
    KHABAROVSK_REGION = "KhabarovskRegion"
    KHANTY_MANSI_AUTONOMOUS_OKRUG = "KhantyMansiAutonomousOkrug"
    CHELYABINSK_REGION = "ChelyabinskRegion"
    CHECHEN_REGION = "ChechenRegion"
    CHUVASH_REGION = "ChuvashRegion"
    CHUKOTKA_AUTONOMOUS_OKRUG = "ChukotkaAutonomousOkrug"
    YAMALO_NENETS_AUTONOMOUS_OKRUG = "YamaloNenetsAutonomousOkrug"
    YAROSLAVL_REGION = "YaroslavlRegion"
    DONETSK_PEOPLE_REPUBLIC = "DonetskPeopleRepublic"
    LUHANSK_PEOPLE_REPUBLIC = "LuhanskPeopleRepublic"
    ZAPOROZHYE_REGION = "ZaporozhyeRegion"
    KHERSON_REGION = "KhersonRegion"


class GraduatedStudentsReportForm(Enum):
    MONITORING_OF_EMPLOYMENT = "MonitoringOfEmployment"
    FIS_FRDO = "FisFrdo"


class LessonDurationType(Enum):
    NONE = "AcademicHour"
    FOR_DAY = "ForDay"
    FOR_LESSON = "ForLesson"


class FreeEducationReason(Enum):
    NONE = "None"
    INTERNATIONAL_AGREEMENT = "InternationalAgreement"
    COMPATRIOT_STATUS = "CompatriotStatus"


class LicenseInfoType(Enum):
    LICENSE = "License"
    ACCREDITATION = "Accreditation"
