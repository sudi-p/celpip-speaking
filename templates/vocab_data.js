window.VOCAB = [
  // ── General (Usable across all tasks) ──
  { word: "Initially", meaning: "At first; replaces the overused at the beginning", example: "Initially, I was nervous, but gradually I grew confident.", type: "General", task: "0" },
  { word: "Gradually", meaning: "Slowly over time; shows a process unfolding", example: "Gradually, I realized that hard work was paying off.", type: "General", task: "0" },
  { word: "Subsequently", meaning: "After that; more formal than then", example: "I completed my degree, and subsequently, I started working.", type: "General", task: "0" },
  { word: "Nevertheless", meaning: "Despite that; stronger contrast than but", example: "The weather was terrible; nevertheless, we went ahead with the plan.", type: "General", task: "0" },
  { word: "In hindsight", meaning: "Looking back now; great for closing reflections", example: "In hindsight, I wish I had started learning languages earlier.", type: "General", task: "0" },
  { word: "Ultimately", meaning: "In the end; finally", example: "Ultimately, the decision was mine to make.", type: "General", task: "0" },
  { word: "Perspective", meaning: "A particular way of viewing things", example: "From my perspective, this is the best approach.", type: "General", task: "0" },
  { word: "Significant", meaning: "Important or noticeable", example: "That experience had a significant impact on my life.", type: "General", task: "0" },
  { word: "Evident", meaning: "Clearly seen or understood", example: "It was evident that the project would succeed.", type: "General", task: "0" },
  { word: "Remarkable", meaning: "Worthy of attention; striking", example: "Her progress was remarkable in just a few months.", type: "General", task: "0" },

  // ── Task 1: Giving Advice ──
  { word: "Prudent", meaning: "Wise and careful in decision-making", example: "It's prudent to save money before making major purchases.", type: "Advice & Guidance", task: "1" },
  { word: "Remedy", meaning: "A solution to a problem; a treatment", example: "The best remedy for stress is regular exercise.", type: "Advice & Guidance", task: "1" },
  { word: "Elaborate", meaning: "To explain in detail; add more information", example: "Can you elaborate on your main point?", type: "Advice & Guidance", task: "1" },
  { word: "Mitigate", meaning: "To make something less severe", example: "Wearing sunscreen helps mitigate sun damage.", type: "Advice & Guidance", task: "1" },
  { word: "Feasible", meaning: "Possible to do; practicable", example: "The plan is feasible if we have enough budget.", type: "Advice & Guidance", task: "1" },
  { word: "Advocate", meaning: "To recommend or support publicly", example: "I strongly advocate for investing in education.", type: "Advice & Guidance", task: "1" },

  // ── Task 2: Personal Experience ──
  { word: "Exhilarating", meaning: "Thrilling and exciting", example: "Skydiving for the first time was absolutely exhilarating.", type: "Emotions & Reactions", task: "2" },
  { word: "Humbling", meaning: "Making you feel small in a meaningful way", example: "Volunteering was a humbling experience that changed me.", type: "Emotions & Reactions", task: "2" },
  { word: "Apprehensive", meaning: "Slightly anxious, unsure of what's coming", example: "I felt apprehensive before my first day at university.", type: "Emotions & Reactions", task: "2" },
  { word: "Awestruck", meaning: "Overwhelmed by something impressive or beautiful", example: "We were awestruck when we saw the Northern Lights.", type: "Emotions & Reactions", task: "2" },
  { word: "Relieved", meaning: "Free from worry after something resolves", example: "When I passed the exam, I felt completely relieved.", type: "Emotions & Reactions", task: "2" },
  { word: "Poignant", meaning: "Evoking sadness or regret; deeply moving", example: "The film had a poignant ending that touched everyone.", type: "Emotions & Reactions", task: "2" },
  { word: "Immersive", meaning: "Completely surrounding you; an immersive environment", example: "The museum created an immersive experience with interactive displays.", type: "Describing the Experience", task: "2" },
  { word: "Spontaneous", meaning: "Unplanned, happening naturally in the moment", example: "We made a spontaneous decision to drive to the coast.", type: "Describing the Experience", task: "2" },
  { word: "Surreal", meaning: "Felt strange, almost too good or odd to be real", example: "Meeting my favorite celebrity felt completely surreal.", type: "Describing the Experience", task: "2" },
  { word: "Reminisce", meaning: "To recall and think about past experiences", example: "We spent the evening reminiscing about our university days.", type: "Reflection & Lessons", task: "2" },
  { word: "Pivotal", meaning: "A turning point; a pivotal moment", example: "That conversation was a pivotal moment in my career.", type: "Reflection & Lessons", task: "2" },
  { word: "Transformative", meaning: "Changed you in a meaningful way", example: "The program was transformative for my development.", type: "Reflection & Lessons", task: "2" },
  { word: "Gratifying", meaning: "Deeply satisfying and rewarding", example: "Seeing my hard work pay off was incredibly gratifying.", type: "Reflection & Lessons", task: "2" },

  // ── Task 3: Describing a Scene ──
  { word: "Vibrant", meaning: "Bright, vivid, and full of energy", example: "The vibrant colors of the market caught everyone's attention.", type: "Describing Places & Scenes", task: "3" },
  { word: "Bustling", meaning: "Full of busy or noisy activity", example: "The bustling streets of Tokyo were overwhelming at first.", type: "Describing Places & Scenes", task: "3" },
  { word: "Serene", meaning: "Calm, peaceful, and undisturbed", example: "The serene lake reflected the mountains perfectly.", type: "Describing Places & Scenes", task: "3" },
  { word: "Adjacent", meaning: "Next to or adjoining something else", example: "The hotel was adjacent to the beach.", type: "Describing Places & Scenes", task: "3" },
  { word: "Picturesque", meaning: "Visually attractive and charming", example: "The village was picturesque with its stone cottages.", type: "Describing Places & Scenes", task: "3" },
  { word: "Sprawling", meaning: "Spreading over a large area", example: "The sprawling garden covered several acres.", type: "Describing Places & Scenes", task: "3" },
  { word: "Desolate", meaning: "Empty and lonely; barren", example: "The desolate beach was peaceful in the early morning.", type: "Describing Places & Scenes", task: "3" },
  { word: "Crowded", meaning: "Filled with many people", example: "The crowded train made it difficult to move.", type: "Describing Places & Scenes", task: "3" },

  // ── Task 4: Making Predictions ──
  { word: "Anticipate", meaning: "To expect or predict something", example: "I anticipate that technology will transform industries.", type: "Predictions & Possibilities", task: "4" },
  { word: "Inevitable", meaning: "Certain to happen; unavoidable", example: "Change is inevitable in a fast-moving world.", type: "Predictions & Possibilities", task: "4" },
  { word: "Plausible", meaning: "Seeming reasonable or probable", example: "The explanation seems plausible but needs verification.", type: "Predictions & Possibilities", task: "4" },
  { word: "Emerging", meaning: "Beginning to appear or become known", example: "Emerging technologies are reshaping society.", type: "Predictions & Possibilities", task: "4" },
  { word: "Unprecedented", meaning: "Never done or known before; novel", example: "The pandemic presented unprecedented global challenges.", type: "Predictions & Possibilities", task: "4" },
  { word: "Likely", meaning: "Probable; probably going to happen", example: "It's likely that prices will increase next year.", type: "Predictions & Possibilities", task: "4" },
  { word: "Trajectory", meaning: "The path or direction something is following", example: "The company's growth trajectory is impressive.", type: "Predictions & Possibilities", task: "4" },
  { word: "Accelerate", meaning: "To increase in speed or intensity", example: "Climate change will accelerate if we don't act.", type: "Predictions & Possibilities", task: "4" },

  // ── Task 5: Comparing & Persuading ──
  { word: "Whereas", meaning: "In contrast to; on the other hand", example: "Whereas my brother enjoys sports, I prefer reading.", type: "Comparison & Contrast", task: "5" },
  { word: "Moreover", meaning: "In addition; furthermore", example: "The job offers great salary. Moreover, benefits are excellent.", type: "Comparison & Contrast", task: "5" },
  { word: "Analogous", meaning: "Comparable in certain respects", example: "Learning languages is analogous to learning music.", type: "Comparison & Contrast", task: "5" },
  { word: "Diverge", meaning: "To differ or move in different directions", example: "Our opinions on education diverge significantly.", type: "Comparison & Contrast", task: "5" },
  { word: "Juxtapose", meaning: "To place side by side for comparison", example: "The artist juxtaposed traditional and modern styles.", type: "Comparison & Contrast", task: "5" },
  { word: "Compelling", meaning: "Convincing and persuasive", example: "The documentary presents a compelling argument.", type: "Opinion & Persuasion", task: "5" },
  { word: "Contend", meaning: "To argue or claim firmly", example: "Experts contend that remote work boosts productivity.", type: "Opinion & Persuasion", task: "5" },
  { word: "Substantiate", meaning: "To support with evidence or proof", example: "The researcher substantiated her claims with data.", type: "Opinion & Persuasion", task: "5" },
  { word: "Entail", meaning: "To involve as a necessary consequence", example: "The job would entail relocating to another city.", type: "Cause & Effect", task: "5" },

  // ── Task 6: Difficult Situation ──
  { word: "Predicament", meaning: "A difficult, complicated, or embarrassing situation", example: "I found myself in a predicament when my car broke down.", type: "Difficulty & Challenges", task: "6" },
  { word: "Daunting", meaning: "Intimidating but not impossible", example: "Moving abroad was daunting, but I managed.", type: "Difficulty & Challenges", task: "6" },
  { word: "Persevere", meaning: "To continue steadily despite difficulty", example: "Despite obstacles, we persevered until completion.", type: "Difficulty & Challenges", task: "6" },
  { word: "Dilemma", meaning: "A situation with two equally difficult options", example: "I faced a dilemma: accept the job or stay close to family.", type: "Difficulty & Challenges", task: "6" },
  { word: "Resilience", meaning: "Ability to recover and keep going", example: "Her resilience after setbacks was truly inspiring.", type: "Difficulty & Challenges", task: "6" },
  { word: "Perseverance", meaning: "Continuing despite difficulty", example: "Her perseverance through rejection led to success.", type: "Difficulty & Challenges", task: "6" },
  { word: "Initiative", meaning: "The ability to start or lead something", example: "She took the initiative to organize the cleanup.", type: "Solutions & Strategies", task: "6" },
  { word: "Resourceful", meaning: "Clever and inventive in dealing with problems", example: "The team was resourceful with a limited budget.", type: "Solutions & Strategies", task: "6" },

  // ── Task 7: Expressing Opinions ──
  { word: "Contentious", meaning: "Causing or likely to cause heated debate", example: "Climate change remains a contentious political issue.", type: "Emotions & Reactions", task: "7" },
  { word: "Justify", meaning: "To provide good reason or explanation", example: "Can you justify why this approach is better?", type: "Opinion & Persuasion", task: "7" },
  { word: "Argue", meaning: "To give reasons for a position", example: "I argue that education should be free for all.", type: "Opinion & Persuasion", task: "7" },
  { word: "Stance", meaning: "A position or opinion on an issue", example: "Her stance on environmental issues is clear.", type: "Opinion & Persuasion", task: "7" },
  { word: "Skeptical", meaning: "Not easily convinced; doubtful", example: "I am skeptical about his promises.", type: "Opinion & Persuasion", task: "7" },
  { word: "Credible", meaning: "Able to be believed; trustworthy", example: "The source is credible and well-researched.", type: "Opinion & Persuasion", task: "7" },
  { word: "Paramount", meaning: "Of supreme importance; supreme", example: "Honesty is paramount in all relationships.", type: "Opinion & Persuasion", task: "7" },
  { word: "Cogent", meaning: "Clear, logical, and convincing", example: "The speaker made a cogent argument.", type: "Opinion & Persuasion", task: "7" },

  // ── Task 8: Unusual Situation ──
  { word: "Unprecedented", meaning: "Never done or known before; novel", example: "The situation was unprecedented in our company's history.", type: "Predictions & Possibilities", task: "8" },
  { word: "Improvise", meaning: "To create without preparation", example: "When equipment failed, the musician had to improvise.", type: "Solutions & Strategies", task: "8" },
  { word: "Unforeseen", meaning: "Not expected or anticipated", example: "An unforeseen problem delayed the project.", type: "Difficulty & Challenges", task: "8" },
  { word: "Adapting", meaning: "Adjusting to new conditions", example: "Adapting to the new system was challenging.", type: "Solutions & Strategies", task: "8" },
  { word: "Ingenious", meaning: "Clever and creative", example: "She came up with an ingenious solution.", type: "Solutions & Strategies", task: "8" },
  { word: "Bewildering", meaning: "Confusing and disorienting", example: "The situation was bewildering at first.", type: "Emotions & Reactions", task: "8" },
  { word: "Volatile", meaning: "Liable to change rapidly; unstable", example: "The situation was volatile and unpredictable.", type: "Difficulty & Challenges", task: "8" },
  { word: "Catastrophic", meaning: "Involving sudden great damage or disaster", example: "The failure would have been catastrophic.", type: "Difficulty & Challenges", task: "8" },
];
