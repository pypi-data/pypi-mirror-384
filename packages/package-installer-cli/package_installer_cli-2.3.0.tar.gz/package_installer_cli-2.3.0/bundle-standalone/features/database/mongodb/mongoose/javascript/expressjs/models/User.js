import mongoose from "mongoose";

const UserSchema = new mongoose.Schema({
  name: String,
  email: { type: String, unique: true },
  password: { type: String, select: false },
});

export default mongoose.models.User || mongoose.model("User", UserSchema);
