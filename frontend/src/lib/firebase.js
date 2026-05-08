import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider, signInWithPopup } from "firebase/auth";

const firebaseConfig = {
  // Get this from Firebase Console → Project Settings → Your apps → Web app
  apiKey: "YOUR_FIREBASE_API_KEY",
  authDomain: "namma-city-1c3ca.firebaseapp.com",
  projectId: "namma-city-1c3ca",
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);

export async function signInWithGoogle() {
  const provider = new GoogleAuthProvider();
  const result = await signInWithPopup(auth, provider);
  return {
    name: result.user.displayName,
    email: result.user.email,
    photo: result.user.photoURL,
  };
}
