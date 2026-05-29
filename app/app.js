const suggestedIngredients = [
  "chicken", "ground beef", "eggs", "milk", "cheese", "yogurt", "rice", "pasta",
  "bread", "potatoes", "tomatoes", "spinach", "broccoli", "carrots", "onion", "garlic",
  "bell pepper", "frozen peas", "beans", "tortillas", "salmon", "tofu"
];

const recipes = [
  {
    name: "Creamy Fridge Pasta Bake",
    emoji: "🍝",
    time: "30 min",
    level: "Easy",
    ingredients: ["pasta", "cheese", "milk", "broccoli", "chicken", "onion", "garlic"],
    summary: "A cozy pasta bake that uses leftover dairy, vegetables, and cooked meat.",
    steps: [
      "Boil pasta until just tender and save half a cup of pasta water.",
      "Sauté onion, garlic, broccoli, and chicken until hot and fragrant.",
      "Stir in milk, cheese, and pasta water to make a quick creamy sauce.",
      "Fold in pasta, top with more cheese, and broil until golden."
    ]
  },
  {
    name: "Freezer Fried Rice",
    emoji: "🍚",
    time: "20 min",
    level: "Beginner",
    ingredients: ["rice", "eggs", "frozen peas", "carrots", "onion", "garlic", "chicken", "tofu"],
    summary: "Turns leftover rice and freezer vegetables into a fast dinner.",
    steps: [
      "Scramble eggs in a hot skillet, then remove them to a plate.",
      "Cook onion, garlic, carrots, and frozen peas until tender.",
      "Add cold rice and press it into the pan so it lightly crisps.",
      "Return eggs and protein, season to taste, and serve hot."
    ]
  },
  {
    name: "Loaded Breakfast Tacos",
    emoji: "🌮",
    time: "15 min",
    level: "Easy",
    ingredients: ["tortillas", "eggs", "cheese", "tomatoes", "spinach", "bell pepper", "beans"],
    summary: "A flexible breakfast-for-dinner idea for eggs, vegetables, and tortillas.",
    steps: [
      "Warm tortillas in a dry pan and keep them covered.",
      "Cook bell pepper, spinach, tomatoes, or beans until warm.",
      "Scramble eggs gently with cheese until soft and creamy.",
      "Fill tortillas, add toppings, and fold into tacos."
    ]
  },
  {
    name: "One-Pan Chicken Potato Skillet",
    emoji: "🍗",
    time: "35 min",
    level: "Simple",
    ingredients: ["chicken", "potatoes", "carrots", "onion", "garlic", "broccoli"],
    summary: "A hearty skillet meal for chicken and sturdy fridge vegetables.",
    steps: [
      "Dice potatoes and carrots small so they cook quickly.",
      "Brown chicken pieces in a large skillet, then set aside.",
      "Cook potatoes, carrots, onion, and garlic until tender.",
      "Return chicken, cover briefly, and finish with herbs or lemon."
    ]
  },
  {
    name: "Tomato Bean Soup",
    emoji: "🍲",
    time: "25 min",
    level: "Easy",
    ingredients: ["tomatoes", "beans", "onion", "garlic", "carrots", "spinach", "bread"],
    summary: "A pantry-friendly soup that welcomes soft vegetables and canned beans.",
    steps: [
      "Sauté onion, garlic, and carrots until sweet and softened.",
      "Add tomatoes, beans, and water or broth, then simmer.",
      "Stir in spinach at the end so it stays bright.",
      "Serve with toasted bread or a cheese topping."
    ]
  },
  {
    name: "Salmon Veggie Rice Bowl",
    emoji: "🐟",
    time: "25 min",
    level: "Medium",
    ingredients: ["salmon", "rice", "broccoli", "carrots", "spinach", "bell pepper"],
    summary: "A balanced bowl for fish, grains, and crisp vegetables.",
    steps: [
      "Season salmon and roast or pan-sear until flaky.",
      "Warm rice while steaming or sautéing the vegetables.",
      "Build bowls with rice, vegetables, and salmon pieces.",
      "Finish with yogurt sauce, soy glaze, or lemon."
    ]
  }
];

const state = { selected: new Set(["eggs", "cheese", "rice"]), activeRecipe: null, stepIndex: 0 };

const ingredientPanel = document.querySelector("#suggested-ingredients");
const selectedPanel = document.querySelector("#selected-ingredients");
const recipeResults = document.querySelector("#recipe-results");
const fileInput = document.querySelector("#food-photo");
const previewWrap = document.querySelector(".preview-wrap");
const previewImage = document.querySelector("#preview");
const uploadBox = document.querySelector(".upload-box");

function normalize(value) {
  return value.trim().toLowerCase();
}

function toggleIngredient(ingredient) {
  if (state.selected.has(ingredient)) state.selected.delete(ingredient);
  else state.selected.add(ingredient);
  renderIngredients();
}

function renderIngredients() {
  ingredientPanel.innerHTML = suggestedIngredients.map((ingredient) => `
    <button class="chip ${state.selected.has(ingredient) ? "active" : ""}" type="button" data-ingredient="${ingredient}">${ingredient}</button>
  `).join("");

  selectedPanel.innerHTML = [...state.selected].length
    ? [...state.selected].map((ingredient) => `<button class="chip" type="button" data-selected="${ingredient}" aria-label="Remove ${ingredient}">${ingredient}</button>`).join("")
    : `<p>No ingredients selected yet.</p>`;
}

function scoreRecipe(recipe) {
  const matches = recipe.ingredients.filter((item) => state.selected.has(item));
  return { recipe, matches, score: matches.length / recipe.ingredients.length };
}

function renderRecipes() {
  const ranked = recipes
    .map(scoreRecipe)
    .sort((a, b) => b.matches.length - a.matches.length || b.score - a.score);

  recipeResults.innerHTML = ranked.map(({ recipe, matches }) => `
    <article class="recipe-card">
      <div class="recipe-art" aria-hidden="true">${recipe.emoji}</div>
      <div>
        <h3>${recipe.name}</h3>
        <p>${recipe.summary}</p>
      </div>
      <div class="recipe-meta"><span>⏱ ${recipe.time}</span><span>⭐ ${recipe.level}</span><span>✅ ${matches.length} match${matches.length === 1 ? "" : "es"}</span></div>
      <strong>Uses:</strong>
      <ul>${recipe.ingredients.slice(0, 6).map((item) => `<li>${item}</li>`).join("")}</ul>
      <button class="button primary" type="button" data-watch="${recipe.name}">Watch steps</button>
    </article>
  `).join("");
}

function setActiveRecipe(recipeName) {
  state.activeRecipe = recipes.find((recipe) => recipe.name === recipeName);
  state.stepIndex = 0;
  renderVideoStep();
  document.querySelector("#video").scrollIntoView({ behavior: "smooth", block: "center" });
}

function renderVideoStep() {
  const screen = document.querySelector("#video-screen");
  const title = document.querySelector("#video-title");
  const summary = document.querySelector("#video-summary");

  if (!state.activeRecipe) return;

  const step = state.activeRecipe.steps[state.stepIndex];
  title.textContent = `${state.activeRecipe.name} video guide`;
  summary.textContent = `Step ${state.stepIndex + 1} of ${state.activeRecipe.steps.length}: follow along at your own pace.`;
  screen.innerHTML = `
    <span>${state.activeRecipe.emoji}</span>
    <strong>Step ${state.stepIndex + 1}</strong>
    <p>${step}</p>
  `;
}

ingredientPanel.addEventListener("click", (event) => {
  const button = event.target.closest("[data-ingredient]");
  if (button) toggleIngredient(button.dataset.ingredient);
});

selectedPanel.addEventListener("click", (event) => {
  const button = event.target.closest("[data-selected]");
  if (button) toggleIngredient(button.dataset.selected);
});

document.querySelector("#ingredient-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const input = document.querySelector("#custom-ingredient");
  const ingredient = normalize(input.value);
  if (!ingredient) return;
  state.selected.add(ingredient);
  input.value = "";
  renderIngredients();
});

document.querySelector("#find-recipes").addEventListener("click", () => {
  renderRecipes();
  document.querySelector("#recipes").scrollIntoView({ behavior: "smooth" });
});

recipeResults.addEventListener("click", (event) => {
  const button = event.target.closest("[data-watch]");
  if (button) setActiveRecipe(button.dataset.watch);
});

document.querySelector("#next-step").addEventListener("click", () => {
  if (!state.activeRecipe) return;
  state.stepIndex = (state.stepIndex + 1) % state.activeRecipe.steps.length;
  renderVideoStep();
});

document.querySelector("#prev-step").addEventListener("click", () => {
  if (!state.activeRecipe) return;
  state.stepIndex = (state.stepIndex - 1 + state.activeRecipe.steps.length) % state.activeRecipe.steps.length;
  renderVideoStep();
});

fileInput.addEventListener("change", () => {
  const [file] = fileInput.files;
  if (!file) return;
  previewImage.src = URL.createObjectURL(file);
  previewWrap.hidden = false;
  uploadBox.hidden = true;

  const filenameHints = normalize(file.name).split(/[^a-z]+/).filter(Boolean);
  suggestedIngredients.forEach((ingredient) => {
    const parts = ingredient.split(" ");
    if (parts.some((part) => filenameHints.includes(part))) state.selected.add(ingredient);
  });
  renderIngredients();
});

document.querySelector("#remove-photo").addEventListener("click", () => {
  fileInput.value = "";
  previewImage.removeAttribute("src");
  previewWrap.hidden = true;
  uploadBox.hidden = false;
});

renderIngredients();
renderRecipes();
