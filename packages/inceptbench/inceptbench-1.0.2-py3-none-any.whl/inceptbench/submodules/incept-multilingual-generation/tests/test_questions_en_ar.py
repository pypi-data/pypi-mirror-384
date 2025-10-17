import json
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
"""
Centralized test questions for all image generation tests
"""

TEST_QUESTIONS = {
    "Grade 1": {
        # "Counting and cardinality": {
        #     "english": "What number comes after 119?",
        #     "arabic": "ما العدد الذي يأتي بعد 119؟"
        # },
        # "Place value (ones, tens)": {
        #     "english": "In the number 47, the 4 stands for how many tens?",
        #     "arabic": "في الرقم 47، الرقم 4 يمثل كم عشرة؟"
        # },
        # "Addition and subtraction (within 20)": {
        #     "english": "What is 9 + 6?",
        #     "arabic": "كم يساوي 9 + 6؟"
        # },
        "Word problems (add/sub)": {
            "english": "Eva has 8 apples and eats 2. How many are left?",
            "arabic": "لدى إيفا 8 تفاحات وأكلت 2. كم تفاحة تبقى؟"
        },
        "Equal sign & equations": {
            "english": "Which number makes 7 = __ + 3 true?",
            "arabic": "أي رقم يجعل 7 = __ + 3 صحيحة؟"
        },
        # "Measurement & length": {"english": "Which is longer: a pencil or a paper clip?", "arabic": "أيهما أطول: القلم الرصاص أم مشبك الورق؟"},
        "Time (hour/half-hour)": {
            "english": "If the clock shows 3:30, what time is it?",
            "arabic": "إذا كانت الساعة تُظهر 3:30، فما الوقت؟"
        },
        # "Money": {"english": "Which coin is worth 10 cents?", "arabic": "أي عملة تساوي 10 سنتات؟"},
        "Geometry (2D/3D shapes)": {
            "english": "Which shape has 3 sides?",
            "arabic": "أي شكل له 3 أضلاع؟"
        },
        "Addition - Apples": {
            "english": "Sara has 5 apples and her friend gives her 7 more. How many apples does Sara have now?",
            "arabic": "لدى سارة 5 تفاحات وأعطاها صديقها 7 تفاحات أخرى. كم تفاحة لدى سارة الآن؟"
        },
        "Subtraction - Apples": {
            "english": "Tom had 20 apples and gave 8 to his friends. How many apples does he have left?",
            "arabic": "كان لدى توم 20 تفاحة وأعطى 8 لأصدقائه. كم تفاحة تبقى لديه؟"
        },
        "Division - Apples": {
            "english": "If 24 apples are shared equally among 6 children, how many apples does each child get?",
            "arabic": "إذا تم تقسيم 24 تفاحة بالتساوي بين 6 أطفال، كم تفاحة يحصل كل طفل؟"
        }
    },
    "Grade 2": {
        # "Place value (hundreds, tens, ones)": {
        #     "english": "What digit is in the tens place of 326?",
        #     "arabic": "ما الرقم الموجود في منزلة العشرات في العدد 326؟"
        # },
        "Addition/subtraction within 1000": {
            "english": "What is 542 - 218?",
            "arabic": "كم يساوي 542 - 218؟"
        },
        "Multiplication as repeated addition": {
            "english": "What is 3 groups of 5?",
            "arabic": "كم يساوي 3 مجموعات من 5؟"
        },
        "Measurement (length, weight, capacity)": {
            "english": "Which unit measures liquid: liters or meters?",
            "arabic": "أي وحدة تقيس السوائل: اللترات أم الأمتار؟"
        },
        "Data (bar graphs)": {
            "english": "If 5 students like red and 3 like blue, which bar is taller?",
            "arabic": "إذا كان 5 طلاب يحبون الأحمر و 3 يحبون الأزرق، أي عمود أطول؟"
        },
        "Geometry (shapes & fractions)": {
            "english": "Divide a square into 4 equal parts. What fraction is one part?",
            "arabic": "قسم مربعاً إلى 4 أجزاء متساوية. ما الكسر الذي يمثل جزءاً واحداً؟"
        },
        "Addition - Pizza": {
            "english": "A pizza shop sold 12 pizzas in the morning and 18 pizzas in the evening. How many pizzas were sold in total?",
            "arabic": "باع محل بيتزا 12 بيتزا في الصباح و 18 بيتزا في المساء. كم بيتزا بيعت في المجموع؟"
        },
        "Subtraction - Pizza": {
            "english": "Out of 15 pizzas, 9 were eaten at a party. How many pizzas are left?",
            "arabic": "من أصل 15 بيتزا، تم أكل 9 في حفلة. كم بيتزا تبقت؟"
        },
        "Multiplication - Apples": {
            "english": "A basket has 6 apples, and there are 4 baskets. How many apples are there in total?",
            "arabic": "في السلة الواحدة 6 تفاحات، وهناك 4 سلال. كم تفاحة في المجموع؟"
        },
        "Division - Pizza": {
            "english": "A pizza has 12 slices. If 4 friends share it equally, how many slices does each get?",
            "arabic": "للبيتزا 12 قطعة. إذا تقاسمها 4 أصدقاء بالتساوي، كم قطعة يحصل كل واحد؟"
        }
    },
    "Grade 3": {
        "Multiplication and division": {
            "english": "What is 6 × 7?",
            "arabic": "كم يساوي 6 × 7؟"
        },
        "Properties of multiplication": {
            "english": "Which property says 3 × 4 = 4 × 3?",
            "arabic": "أي خاصية تقول أن 3 × 4 = 4 × 3؟"
        },
        "Area and perimeter": {
            "english": "What is the area of a 5 by 3 rectangle?",
            "arabic": "ما مساحة مستطيل أبعاده 5 في 3؟"
        },
        "Fractions": {
            "english": "Which fraction is larger: 1/2 or 1/3?",
            "arabic": "أي كسر أكبر: 1/2 أم 1/3؟"
        },
        "Measurement (time, volume, mass)": {
            "english": "How many minutes are in 1 hour?",
            "arabic": "كم دقيقة في الساعة الواحدة؟"
        },
        "Geometry": {
            "english": "How many sides does a quadrilateral have?",
            "arabic": "كم ضلعاً للشكل رباعي الأضلاع؟"
        },
        "Addition - Bags": {
            "english": "A store had 45 bags on Monday and received 30 more on Tuesday. How many bags are there now?",
            "arabic": "كان لدى متجر 45 حقيبة يوم الاثنين واستلم 30 حقيبة أخرى يوم الثلاثاء. كم حقيبة موجودة الآن؟"
        },
        "Subtraction - Bags": {
            "english": "A shop had 50 bags but sold 23. How many bags remain?",
            "arabic": "كان لدى متجر 50 حقيبة لكنه باع 23 حقيبة. كم حقيبة تبقت؟"
        },
        "Multiplication - Pizza": {
            "english": "Each pizza box contains 8 slices. How many slices are there in 5 boxes?",
            "arabic": "كل علبة بيتزا تحتوي على 8 قطع. كم قطعة في 5 علب؟"
        },
        "Multiplication - Bags": {
            "english": "Each student carries 3 bags, and there are 10 students. How many bags are there in all?",
            "arabic": "كل طالب يحمل 3 حقائب، وهناك 10 طلاب. كم حقيبة في المجموع؟"
        },
        "Division - Bags": {
            "english": "A shipment of 60 bags needs to be packed equally into 5 cartons. How many bags go in each carton?",
            "arabic": "يحتاج تعبئة 60 حقيبة بالتساوي في 5 كراتين. كم حقيبة تدخل في كل كرتون؟"
        }
    },
    "Grade 4": {
        "Multi-digit multiplication": {
            "english": "What is 23 × 5?",
            "arabic": "كم يساوي 23 × 5؟"
        },
        "Long division": {
            "english": "What is 84 ÷ 7?",
            "arabic": "كم يساوي 84 ÷ 7؟"
        },
        "Factors and multiples": {
            "english": "Which is a factor of 18?",
            "arabic": "أي رقم هو عامل من عوامل 18؟"
        },
        "Fractions": {
            "english": "Which fraction equals 2/4?",
            "arabic": "أي كسر يساوي 2/4؟"
        },
        "Decimals": {
            "english": "What is 0.5 as a fraction?",
            "arabic": "ما هو 0.5 ككسر؟"
        },
        "Angles": {
            "english": "How many degrees are in a right angle?",
            "arabic": "كم درجة في الزاوية القائمة؟"
        },
        "Symmetry": {
            "english": "Which shape has 4 lines of symmetry: square or triangle?",
            "arabic": "أي شكل له 4 خطوط تماثل: المربع أم المثلث؟"
        }
    },
    "Grade 5": {
        "Division (2-digit divisors)": {
            "english": "What is 144 ÷ 12?",
            "arabic": "كم يساوي 144 ÷ 12؟"
        },
        "Fractions": {
            "english": "What is 1/2 + 1/4?",
            "arabic": "كم يساوي 1/2 + 1/4؟"
        },
        "Decimals": {
            "english": "What is 0.3 + 0.4?",
            "arabic": "كم يساوي 0.3 + 0.4؟"
        },
        "Volume": {
            "english": "What is the volume of a 2×3×4 box?",
            "arabic": "ما حجم صندوق أبعاده 2×3×4؟"
        },
        "Coordinate plane": {
            "english": "What are the coordinates of a point 3 right and 2 up?",
            "arabic": "ما إحداثيات نقطة على بُعد 3 يميناً و 2 لأعلى؟"
        },
        "Geometry (shapes)": {
            "english": "Which shape has all sides equal and all angles equal?",
            "arabic": "أي شكل له جميع الأضلاع متساوية وجميع الزوايا متساوية؟"
        },
        "Rectangle - Area": {
            "english": "What is the area of a rectangle with length 8 cm and width 6 cm?",
            "arabic": "ما مساحة مستطيل طوله 8 سم وعرضه 6 سم؟"
        },
        "Rectangle - Perimeter": {
            "english": "What is the perimeter of a rectangle with sides 12 cm and 5 cm?",
            "arabic": "ما محيط مستطيل أضلاعه 12 سم و 5 سم؟"
        },
        "Triangle - Right Area": {
            "english": "What is the area of a right triangle with base 10 cm and height 6 cm?",
            "arabic": "ما مساحة مثلث قائم الزاوية قاعدته 10 سم وارتفاعه 6 سم؟"
        },
        # "Triangle - Equilateral Area": {"english": "What is the area of an equilateral triangle with base 10 cm and height 6 cm?", "arabic": "ما مساحة مثلث متساوي الأضلاع قاعدته 10 سم وارتفاعه 6 سم؟"},
        "Triangle - Isoceles Area": {
            "english": "What is the area of an isoceles triangle with base 10 cm and height 6 cm?",
            "arabic": "ما مساحة مثلث متساوي الساقين قاعدته 10 سم وارتفاعه 6 سم؟"
        },
        "Circle - Area": {
            "english": "What is the area of a circle with radius 7 cm?",
            "arabic": "ما مساحة دائرة نصف قطرها 7 سم؟"
        },
        "Circle - Circumference": {
            "english": "What is the circumference of a circle with diameter 14 cm?",
            "arabic": "ما محيط دائرة قطرها 14 سم؟"
        },
        "Triangle - Area": {
            "english": "What is the area of a triangle with base 10 cm and height 6 cm?",
            "arabic": "ما مساحة مثلث قاعدته 10 سم وارتفاعه 6 سم؟"
        },
        # "Equilateral Triangle - Angles": {"english": "What is the measure of each angle in an equilateral triangle?", "arabic": "كم درجة كل زاوية في المثلث متساوي الأضلاع؟"},
        "Equilateral Triangle - Perimeter": {
            "english": "If the side length of an equilateral triangle is 8 cm, what is its perimeter?",
            "arabic": "إذا كان طول ضلع مثلث متساوي الأضلاع 8 سم، فما محيطه؟"
        }
        # "Equilateral Triangle - Symmetry": {"english": "How many lines of symmetry does an equilateral triangle have?", "arabic": "كم خط تماثل يملك المثلث متساوي الأضلاع؟"}
    },
    "Grade 6": {
        "Ratios and proportions": {
            "english": "What is the ratio of 2 cats to 6 dogs?",
            "arabic": "ما النسبة بين 2 قطة و 6 كلاب؟"
        },
        "Division of fractions": {
            "english": "What is 1/2 ÷ 1/4?",
            "arabic": "كم يساوي 1/2 ÷ 1/4؟"
        },
        "Integers": {
            "english": "What is -3 + 5?",
            "arabic": "كم يساوي -3 + 5؟"
        },
        "Equations": {
            "english": "Solve x + 4 = 7",
            "arabic": "حل المعادلة x + 4 = 7"
        },
        "Statistics": {
            "english": "What is the mean of 2, 4, 6?",
            "arabic": "ما متوسط الأرقام 2، 4، 6؟"
        },
        "Geometry": {
            "english": "What is the area of a triangle with base 6 and height 4?",
            "arabic": "ما مساحة مثلث قاعدته 6 وارتفاعه 4؟"
        },
        "Cube - Volume": {
            "english": "What is the volume of a cube with side length 4 cm?",
            "arabic": "ما حجم مكعب طول ضلعه 4 سم؟"
        },
        "Cube - Surface Area": {
            "english": "What is the surface area of a cube with side 5 cm?",
            "arabic": "ما مساحة سطح مكعب طول ضلعه 5 سم؟"
        },
        "Prism - Volume": {
            "english": "What is the volume of a triangular prism with base area 20 cm² and height 15 cm?",
            "arabic": "ما حجم منشور مثلثي مساحة قاعدته 20 سم² وارتفاعه 15 سم؟"
        },
        "Prism - Surface Area": {
            "english": "What is the surface area of a rectangular prism with dimensions 2 cm × 3 cm × 5 cm?",
            "arabic": "ما مساحة سطح منشور مستطيل أبعاده 2 سم × 3 سم × 5 سم؟"
        },
        # "Cube - Volume": {"english": "If the edge of a cube is doubled, by what factor does its volume increase?", "arabic": "إذا تم مضاعفة طول حرف المكعب، بأي عامل يزداد حجمه؟"},
        "Cube - Volume (reverse)": {
            "english": "A cube has volume 125 cm³. What is the length of one side?",
            "arabic": "مكعب حجمه 125 سم³. ما طول ضلع واحد؟"
        },
        # "Cube - Properties": {"english": "How many edges does a cube have?", "arabic": "كم حرفاً يملك المكعب؟"},
        "Prism - Volume": {
            "english": "What is the volume of a prism if its base area is 20 cm² and height 12 cm?",
            "arabic": "ما حجم منشور إذا كانت مساحة قاعدته 20 سم² وارتفاعه 12 سم؟"
        },
        "Prism - Surface Area": {
            "english": "A rectangular prism has dimensions 2 × 4 × 6 cm. What is its surface area?",
            "arabic": "منشور مستطيل أبعاده 2 × 4 × 6 سم. ما مساحة سطحه؟"
        },
        "Prism - Properties": {
            "english": "How many faces does a triangular prism have?",
            "arabic": "كم وجهاً يملك المنشور المثلثي؟"
        },
        "Isosceles Triangle - Perimeter": {
            "english": "In an isosceles triangle, if two sides are 5 cm each and the base is 6 cm, what is the perimeter?",
            "arabic": "في مثلث متساوي الساقين، إذا كان طول كل ضلعين 5 سم والقاعدة 6 سم، فما المحيط؟"
        },
        "Isosceles Triangle - Properties": {
            "english": "How many equal sides does an isosceles triangle have?",
            "arabic": "كم ضلعاً متساوياً يملك المثلث متساوي الساقين؟"
        },
        "Isosceles Triangle - Angles": {
            "english": "If the vertex angle of an isosceles triangle is 40°, what is each base angle?",
            "arabic": "إذا كانت زاوية الرأس في مثلث متساوي الساقين 40°، فما كل زاوية قاعدة؟"
        }
    },
    "Grade 7": {
        "Proportions and percent": {
            "english": "What is 50% of 60?",
            "arabic": "كم يساوي 50% من 60؟"
        },
        "Rational numbers": {
            "english": "What is -8 ÷ 2?",
            "arabic": "كم يساوي -8 ÷ 2؟"
        },
        "Linear equations": {
            "english": "Solve 2x + 3 = 7",
            "arabic": "حل المعادلة 2x + 3 = 7"
        },
        "Angles and triangles": {
            "english": "What is the sum of angles in a triangle?",
            "arabic": "ما مجموع زوايا المثلث؟"
        },
        "Probability": {
            "english": "If you flip a coin, what's the chance of heads?",
            "arabic": "إذا ألقيت عملة معدنية، فما احتمال ظهور الوجه؟"
        },
        "Statistics": {
            "english": "Which sample is random: picking every 10th student or picking friends?",
            "arabic": "أي عينة عشوائية: اختيار كل طالب عاشر أم اختيار الأصدقاء؟"
        },
        "Venn Diagrams": {
            "english": "In a class of 20 students, 12 like football, 8 like basketball, and 5 like both. How many students like only football?",
            "arabic": "في فصل من 20 طالباً، 12 يحبون كرة القدم، 8 يحبون كرة السلة، و 5 يحبون الاثنتين. كم طالباً يحب كرة القدم فقط؟"
        },
        "Venn Diagrams 2": {
            "english": "If 15 students study math, 10 study science, and 6 study both, how many study only science?",
            "arabic": "إذا كان 15 طالباً يدرسون الرياضيات، 10 يدرسون العلوم، و 6 يدرسون الاثنين، كم يدرس العلوم فقط؟"
        },
        "Venn Diagrams 3": {
            "english": "In a class: 15 like cricket, 12 like football, 10 like tennis, and 3 like all three. Which region represents those who like exactly two sports?",
            "arabic": "في فصل: 15 يحبون الكريكيت، 12 يحبون كرة القدم، 10 يحبون التنس، و 3 يحبون الثلاثة. أي منطقة تمثل من يحب رياضتين بالضبط؟"
        },
        "Venn Diagrams 4": {
            "english": "In a survey: 40 like Math, 35 like Science, 25 like English, 20 like History, and 10 like all four. What does the central overlap count?",
            "arabic": "في مسح: 40 يحبون الرياضيات، 35 يحبون العلوم، 25 يحبون الإنجليزية، 20 يحبون التاريخ، و 10 يحبون الأربعة. ماذا يعد التداخل المركزي؟"
        },
        "Venn Diagrams 5": {
            "english": "In a survey of 5 sports, how would you find the number of students who like at least one sport?",
            "arabic": "في مسح عن 5 رياضات، كيف تجد عدد الطلاب الذين يحبون رياضة واحدة على الأقل؟"
        },
        "Charts - Pie": {
            "english": "A pie chart shows favorite fruits: 1/2 like apples, 1/4 like bananas, and 1/4 like grapes. Which fruit is liked by most?",
            "arabic": "يُظهر رسم بياني دائري الفواكه المفضلة: 1/2 يحبون التفاح، 1/4 يحبون الموز، و 1/4 يحبون العنب. أي فاكهة هي الأكثر حباً؟"
        },
        "Charts - Bar": {
            "english": "A bar chart shows class test scores: 5 students scored 100, 8 students scored 90, and 2 students scored 80. Which score was most common?",
            "arabic": "يُظهر رسم بياني بالأعمدة درجات اختبار الفصل: 5 طلاب حصلوا على 100، 8 طلاب حصلوا على 90، و 2 طالبان حصلا على 80. أي درجة كانت الأكثر شيوعاً؟"
        },
        "Charts - Line": {
            "english": "If a line graph shows temperature rising steadily from 10°C at 8 am to 20°C at 12 pm, what is the general trend?",
            "arabic": "إذا أظهر رسم بياني خطي ارتفاع درجة الحرارة بثبات من 10°م في الساعة 8 صباحاً إلى 20°م في الساعة 12 ظهراً، فما الاتجاه العام؟"
        },
        "Cylinder - Volume": {
            "english": "What is the volume of a cylinder with radius 3 cm and height 7 cm?",
            "arabic": "ما حجم أسطوانة نصف قطرها 3 سم وارتفاعها 7 سم؟"
        },
        "Cylinder - Surface Area": {
            "english": "What is the total surface area of a cylinder with radius 2 cm and height 10 cm?",
            "arabic": "ما إجمالي مساحة سطح أسطوانة نصف قطرها 2 سم وارتفاعها 10 سم؟"
        },
        "Sphere - Volume": {
            "english": "What is the volume of a sphere with radius 6 cm?",
            "arabic": "ما حجم كرة نصف قطرها 6 سم؟"
        },
        "Sphere - Surface Area": {
            "english": "What is the surface area of a sphere with radius 5 cm?",
            "arabic": "ما مساحة سطح كرة نصف قطرها 5 سم؟"
        },
        "Sphere - Diameter": {
            "english": "What is the diameter of a sphere with radius 9 cm?",
            "arabic": "ما قطر كرة نصف قطرها 9 سم؟"
        },
        "Sphere - Volume Relation": {
            "english": "If the radius of a sphere doubles, what happens to its volume?",
            "arabic": "إذا تضاعف نصف قطر الكرة، ماذا يحدث لحجمها؟"
        },
        "Sphere - Surface Area Formula": {
            "english": "Which formula gives the surface area of a sphere?",
            "arabic": "أي صيغة تعطي مساحة سطح الكرة؟"
        },
        "Cylinder - Faces": {
            "english": "How many circular faces does a cylinder have?",
            "arabic": "كم وجهاً دائرياً يملك الأسطوانة؟"
        },
        "Cylinder - Volume": {
            "english": "If a cylinder has radius 5 cm and height 10 cm, what is its volume?",
            "arabic": "إذا كان للأسطوانة نصف قطر 5 سم وارتفاع 10 سم، فما حجمها؟"
        },
        # "Cylinder - Scaling": {"english": "When the height of a cylinder is halved but the radius is doubled, what happens to its volume?", "arabic": "عندما ينصف ارتفاع الأسطوانة لكن يتضاعف نصف قطرها، ماذا يحدث لحجمها؟"},
        "Right Triangle - Angles": {
            "english": "What is the sum of the two acute angles in a right triangle?",
            "arabic": "ما مجموع الزاويتين الحادتين في المثلث قائم الزاوية؟"
        },
        "Right Triangle - Hypotenuse": {
            "english": "Which side in a right triangle is opposite the right angle?",
            "arabic": "أي ضلع في المثلث قائم الزاوية يقابل الزاوية القائمة؟"
        },
        "Right Triangle - Complementary Angles": {
            "english": "If one angle in a right triangle is 30°, what is the other acute angle?",
            "arabic": "إذا كانت زاوية في المثلث قائم الزاوية 30°، فما هي الزاوية الحادة الأخرى؟"
        },
        "Pythagorean Theorem - Basic": {
            "english": "In a right triangle with legs 6 cm and 8 cm, what is the hypotenuse?",
            "arabic": "في مثلث قائم الزاوية ذي ضلعين 6 سم و 8 سم، ما هو وتر الزاوية القائمة؟"
        }
        # "Pythagorean Theorem - Formula": {"english": "If a right triangle has sides a, b, and hypotenuse c, which equation shows the Pythagorean theorem?", "arabic": "إذا كان للمثلث قائم الزاوية ضلعان a، b ووتر c، أي معادلة توضح نظرية فيثاغورس؟"},
        # "Pythagorean Theorem - Right Triangle Check": {"english": "Which set of numbers can be the sides of a right triangle: (A) 3,4,5 (B) 2,3,4 (C) 6,7,8 (D) 5,12,13?", "arabic": "أي مجموعة من الأرقام يمكن أن تكون أضلاع مثلث قائم الزاوية: (A) 3,4,5 (B) 2,3,4 (C) 6,7,8 (D) 5,12,13؟"}
    },
    "Grade 8": {
        "Linear equations": {
            "english": "What is the slope of y = 2x + 3?",
            "arabic": "ما ميل الخط y = 2x + 3؟"
        },
        "Systems of equations": {
            "english": "Solve: x + y = 5, x - y = 1",
            "arabic": "حل نظام المعادلات: x + y = 5, x - y = 1"
        },
        "Exponents": {
            "english": "What is 3²?",
            "arabic": "كم يساوي 3²؟"
        },
        "Pythagorean theorem": {
            "english": "If a right triangle has legs 3 and 4, what is the hypotenuse?",
            "arabic": "إذا كان للمثلث قائم الزاوية ضلعان 3 و 4، فما هو وتر الزاوية القائمة؟"
        },
        "Transformations": {
            "english": "What transformation flips a shape over a line?",
            "arabic": "أي تحويل يقلب شكلاً حول خط؟"
        },
        "Functions": {
            "english": "If f(x) = x + 2, what is f(3)?",
            "arabic": "إذا كانت f(x) = x + 2، فما هي f(3)؟"
        },
        "Cone - Volume": {
            "english": "What is the volume of a cone with base radius 4 cm and height 9 cm?",
            "arabic": "ما حجم مخروط نصف قطر قاعدته 4 سم وارتفاعه 9 سم؟"
        },
        "Cone - Surface Area": {
            "english": "What is the curved surface area of a cone with radius 3 cm and slant height 5 cm?",
            "arabic": "ما مساحة السطح المنحني لمخروط نصف قطره 3 سم وارتفاعه المائل 5 سم؟"
        },
        "Triangle - Pythagoras": {
            "english": "If a right triangle has legs 9 cm and 12 cm, what is the length of the hypotenuse?",
            "arabic": "إذا كان للمثلث قائم الزاوية ضلعان 9 سم و 12 سم، فما طول وتر الزاوية القائمة؟"
        },
        "Cone - Apex": {
            "english": "Which part of a cone is called the apex?",
            "arabic": "أي جزء من المخروط يسمى القمة؟"
        },
        "Cone - Faces": {
            "english": "How many faces does a cone have?",
            "arabic": "كم وجهاً يملك المخروط؟"
        },
        "Pyramid - Faces": {
            "english": "How many faces does a square pyramid have?",
            "arabic": "كم وجهاً يملك الهرم مربع القاعدة؟"
        },
        "Pyramid - Volume": {
            "english": "If a pyramid has base area 36 cm² and height 9 cm, what is its volume?",
            "arabic": "إذا كان للهرم مساحة قاعدة 36 سم² وارتفاع 9 سم، فما حجمه؟"
        },
        "Pyramid - Properties": {
            "english": "Which 3D shape has one polygon base and triangular faces meeting at a vertex?",
            "arabic": "أي شكل ثلاثي الأبعاد له قاعدة مضلعة واحدة ووجوه مثلثية تلتقي في رأس؟"
        },
        "Pythagorean Theorem - Hypotenuse": {
            "english": "In a right triangle with legs 5 cm and 12 cm, what is the hypotenuse?",
            "arabic": "في مثلث قائم الزاوية ذي ضلعين 5 سم و 12 سم، ما هو وتر الزاوية القائمة؟"
        },
        # "Pythagorean Theorem - Formula": {"english": "Which formula expresses the Pythagorean theorem?", "arabic": "أي صيغة تعبر عن نظرية فيثاغورس؟"},
        "Pythagorean Theorem - Missing Side": {
            "english": "If the hypotenuse of a right triangle is 13 cm and one leg is 5 cm, what is the other leg?",
            "arabic": "إذا كان وتر الزاوية القائمة في مثلث قائم الزاوية 13 سم وضلع واحد 5 سم، فما الضلع الآخر؟"
        },
        "Pythagorean Theorem - Reverse": {
            "english": "In a right triangle, the hypotenuse is 25 cm and one leg is 24 cm. What is the other leg?",
            "arabic": "في مثلث قائم الزاوية، وتر الزاوية القائمة 25 سم وضلع واحد 24 سم. ما الضلع الآخر؟"
        },
        "Pythagorean Theorem - Word Problem": {
            "english": "A ladder 10 m long leans against a wall with its base 6 m from the wall. How high up the wall does it reach?",
            "arabic": "سلم طوله 10 م يرتكز على جدار وقاعدته على بُعد 6 م من الجدار. إلى أي ارتفاع يصل على الجدار؟"
        }
    },
    "Grade 9": {
        "Pyramid - Volume": {
            "english": "What is the volume of a square pyramid with base side 6 cm and height 10 cm?",
            "arabic": "ما حجم هرم مربع القاعدة طول ضلع قاعدته 6 سم وارتفاعه 10 سم؟"
        },
        "Pyramid - Surface Area": {
            "english": "What is the surface area of a square pyramid with base side 8 cm and slant height 10 cm?",
            "arabic": "ما مساحة سطح هرم مربع القاعدة طول ضلع قاعدته 8 سم وارتفاعه المائل 10 سم؟"
        },
        # "Pythagorean Theorem - Coordinate Geometry": {"english": "What is the distance between the points (1,2) and (7,5)?", "arabic": "ما المسافة بين النقطتين (1,2) و (7,5)؟"},
        "Pythagorean Theorem - Real Life": {
            "english": "A 13 m wire supports a pole that is 12 m tall. How far from the base of the pole is the wire anchored?",
            "arabic": "سلك طوله 13 م يدعم عموداً ارتفاعه 12 م. على أي بُعد من قاعدة العمود يرتبط السلك؟"
        },
        "Pythagorean Theorem - Exact Values": {
            "english": "In a right triangle, if one leg is √3 and the hypotenuse is 2, what is the other leg?",
            "arabic": "في مثلث قائم الزاوية، إذا كان ضلع واحد يساوي √3 ووتر الزاوية القائمة 2، فما الضلع الآخر؟"
        }
    },
    "Grade 10": {
        "Pythagorean Theorem - 3D Diagonal": {
            "english": "A rectangular box has length 3 cm, width 4 cm, and height 12 cm. What is the length of its space diagonal?",
            "arabic": "صندوق مستطيل طوله 3 سم وعرضه 4 سم وارتفاعه 12 سم. ما طول قطره الفراغي؟"
        },
        "Pythagorean Theorem - Squares": {
            "english": "A square has diagonal length 10 cm. What is the side length of the square?",
            "arabic": "مربع طول قطره 10 سم. ما طول ضلع المربع؟"
        }
        # "Pythagorean Theorem - Proof Idea": "How can you prove the Pythagorean theorem using the areas of squares on the triangle’s sides?"
    },
    "Algebra I": {
        "Expressions": {
            "english": "Simplify: 2x + 3x",
            "arabic": "بسط: 2x + 3x"
        },
        "Polynomials": {
            "english": "What is (x + 2)(x + 3)?",
            "arabic": "كم يساوي (x + 2)(x + 3)؟"
        },
        "Quadratics": {
            "english": "Solve x² = 9",
            "arabic": "حل x² = 9"
        },
        "Exponents": {
            "english": "What is (2³)?",
            "arabic": "كم يساوي (2³)؟"
        },
        "Rational expressions": {
            "english": "What is 6/x ÷ 2/x?",
            "arabic": "كم يساوي 6/x ÷ 2/x؟"
        },
        "Systems": {
            "english": "Solve by substitution: y = x + 1, y = 2x",
            "arabic": "حل بالتعويض: y = x + 1, y = 2x"
        },
        "Radical expressions": {
            "english": "Simplify: √16",
            "arabic": "بسط: √16"
        },
        "Exponential functions": {
            "english": "If f(x) = 2ˣ, what is f(0)?",
            "arabic": "إذا كانت f(x) = 2ˣ، فما هي f(0)؟"
        }
    },
    "Geometry": {
        "Lines and angles": {
            "english": "If two angles add to 90°, what are they called?",
            "arabic": "إذا كان مجموع زاويتين 90°، ماذا يسميان؟"
        },
        "Triangles": {
            "english": "Which triangle has sides 3, 4, 5?",
            "arabic": "أي مثلث له أضلاع 3، 4، 5؟"
        },
        "Quadrilaterals": {
            "english": "Which quadrilateral has all sides equal?",
            "arabic": "أي شكل رباعي الأضلاع له جميع الأضلاع متساوية؟"
        },
        "Circles": {
            "english": "What is the formula for circumference?",
            "arabic": "ما صيغة محيط الدائرة؟"
        },
        "Area": {
            "english": "What is the area of a circle with radius 3?",
            "arabic": "ما مساحة دائرة نصف قطرها 3؟"
        },
        "Volume": {
            "english": "What is the volume of a sphere with radius 2?",
            "arabic": "ما حجم كرة نصف قطرها 2؟"
        },
        "Similarity": {
            "english": "If triangles are similar with ratio 2:1, how do areas compare?",
            "arabic": "إذا كان المثلثان متشابهين بنسبة 2:1، فكيف تتقارن مساحتاهما؟"
        },
        "Transformations": {
            "english": "What transformation rotates 90° clockwise?",
            "arabic": "أي تحويل يدور 90° باتجاه عقارب الساعة؟"
        }
    },
    "Algebra II": {
        "Complex numbers": {
            "english": "What is i²?",
            "arabic": "كم يساوي i²؟"
        },
        "Polynomials": {
            "english": "What is the degree of x³ + 2x - 1?",
            "arabic": "ما درجة كثيرة الحدود x³ + 2x - 1؟"
        },
        "Rational functions": {
            "english": "What is the domain of f(x) = 1/x?",
            "arabic": "ما مجال الدالة f(x) = 1/x؟"
        },
        "Logarithms": {
            "english": "Solve: log₂(8) = ?",
            "arabic": "حل: log₂(8) = ؟"
        },
        "Sequences": {
            "english": "Find the 10th term of 2, 4, 6, 8...",
            "arabic": "جد الحد العاشر في المتتالية 2، 4، 6، 8..."
        },
        "Matrices": {
            "english": "What is the determinant of [[2,1],[3,4]]?",
            "arabic": "ما محدد المصفوفة [[2,1],[3,4]]؟"
        },
        "Conic sections": {
            "english": "What shape is x² + y² = 9?",
            "arabic": "أي شكل هو x² + y² = 9؟"
        }
    },
    "Pre-Calculus": {
        "Trigonometry": {
            "english": "What is sin(90°)?",
            "arabic": "كم يساوي sin(90°)؟"
        },
        "Functions": {
            "english": "Is f(x) = x² even or odd?",
            "arabic": "هل الدالة f(x) = x² زوجية أم فردية؟"
        },
        "Vectors": {
            "english": "What is the magnitude of vector (3, 4)?",
            "arabic": "ما مقدار المتجه (3, 4)؟"
        },
        "Polar coordinates": {
            "english": "Convert (1, π/2) to rectangular",
            "arabic": "حول (1, π/2) إلى إحداثيات مستطيلة"
        },
        "Sequences and series": {
            "english": "What is the sum of 1 + 2 + 3 + ... + 100?",
            "arabic": "ما مجموع 1 + 2 + 3 + ... + 100؟"
        },
        "Limits (introduction)": {
            "english": "What is lim(x→0) sin(x)/x?",
            "arabic": "كم يساوي lim(x→0) sin(x)/x؟"
        }
    },
    "Grade 11": {
        "Limits": {
            "english": "Find lim(x→2) (x² - 4)/(x - 2)",
            "arabic": "جد lim(x→2) (x² - 4)/(x - 2)"
        },
        "Continuity": {
            "english": "Is f(x) = 1/x continuous at x = 0?",
            "arabic": "هل الدالة f(x) = 1/x متصلة عند x = 0؟"
        }
    },
    "Grade 12": {
        "Derivatives - Power Rule": {
            "english": "Find d/dx (x³ + 2x)",
            "arabic": "جد d/dx (x³ + 2x)"
        },
        "Derivatives - Applications": {
            "english": "The position of a car is s(t) = t² + 2t. What is its velocity at t = 3?",
            "arabic": "موقع سيارة هو s(t) = t² + 2t. ما هي سرعتها عند t = 3؟"
        },
        "Product Rule": {
            "english": "Find d/dx (x² · e^x)",
            "arabic": "جد d/dx (x² · e^x)"
        },
        "Quotient Rule": {
            "english": "Find d/dx (sin x / x)",
            "arabic": "جد d/dx (sin x / x)"
        },
        "Chain Rule": {
            "english": "Find d/dx (cos(3x))",
            "arabic": "جد d/dx (cos(3x))"
        },
        "Implicit Differentiation": {
            "english": "Find dy/dx if x² + y² = 25",
            "arabic": "جد dy/dx إذا كان x² + y² = 25"
        },
        "Basic Integration": {
            "english": "Evaluate ∫ (2x) dx",
            "arabic": "احسب ∫ (2x) dx"
        },
        "Definite Integral": {
            "english": "Evaluate ∫ from 0 to 2 of x dx",
            "arabic": "احسب ∫ من 0 إلى 2 لـ x dx"
        },
        "Area under curve": {
            "english": "Find the area under y = x² from x = 0 to x = 3",
            "arabic": "جد المساحة تحت المنحنى y = x² من x = 0 إلى x = 3"
        },
        "Integration by substitution": {
            "english": "Evaluate ∫ (2x)(x² + 1)^5 dx",
            "arabic": "احسب ∫ (2x)(x² + 1)^5 dx"
        },
        "Integration by parts": {
            "english": "Evaluate ∫ x e^x dx",
            "arabic": "احسب ∫ x e^x dx"
        }
    },
    "Advanced (College-level Calculus)": {
        "Differential Equations": {
            "english": "Solve dy/dx = y",
            "arabic": "حل dy/dx = y"
        },
        "Series": {
            "english": "Find the sum of the geometric series 1 + 1/2 + 1/4 + ...",
            "arabic": "جد مجموع المتتالية الهندسية 1 + 1/2 + 1/4 + ..."
        },
        "Taylor Series": {
            "english": "Write the first 3 terms of the Maclaurin series for e^x",
            "arabic": "اكتب أول 3 حدود لمتتالية ماكلورين لـ e^x"
        },
        "Multivariable Calculus": {
            "english": "Find ∂/∂x (x²y + y²)",
            "arabic": "جد ∂/∂x (x²y + y²)"
        },
        "Multiple Integrals": {
            "english": "Evaluate ∬ over region R of (x + y) dA where R is a rectangle 0 ≤ x ≤ 1, 0 ≤ y ≤ 1",
            "arabic": "احسب ∬ على المنطقة R لـ (x + y) dA حيث R مستطيل 0 ≤ x ≤ 1, 0 ≤ y ≤ 1"
        }
    }
}
