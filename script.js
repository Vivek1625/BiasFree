import { auth, db } from "./firebase.js";
import { GEMINI_API_KEY } from "./config.js";
import { GoogleGenerativeAI } from "https://esm.run/@google/generative-ai";

console.log("Firebase connected:", auth);
console.log("Firestore connected:", db);
console.log("Gemini key loaded:", GEMINI_API_KEY);


const genAI = new GoogleGenerativeAI(GEMINI_API_KEY);

const model = genAI.getGenerativeModel({
    model: "gemini-1.5-flash"
});