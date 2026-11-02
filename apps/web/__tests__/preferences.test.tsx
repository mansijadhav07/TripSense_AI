import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import PreferencesPage from "@/app/preferences/page";
import { fetchUserPreferences, updateUserPreferences } from "@/lib/api";

vi.mock("@/lib/auth", () => ({
  useAuth: () => ({ token: "test-token" }),
}));

vi.mock("@/lib/api", () => ({
  TRAVEL_STYLES: ["family", "business", "romantic", "budget", "luxury", "adventure"],
  fetchUserPreferences: vi.fn(),
  updateUserPreferences: vi.fn(),
}));

const initialPreferences = {
  destination: "Paris",
  min_rating: 4,
  travel_style: "business",
  cleanliness_weight: 2,
  location_weight: 1,
  rooms_weight: 1,
  service_weight: 1,
  value_weight: 1,
  sleep_quality_weight: 1,
};

describe("preferences page", () => {
  beforeEach(() => {
    vi.mocked(fetchUserPreferences).mockResolvedValue(initialPreferences);
    vi.mocked(updateUserPreferences).mockImplementation(async (_token, preferences) => preferences);
  });

  it("loads saved settings and persists edits", async () => {
    render(<PreferencesPage />);

    const destination = await screen.findByLabelText("Preferred destination");
    expect(destination).toHaveValue("Paris");
    expect(screen.getByLabelText("Travel style")).toHaveValue("business");

    fireEvent.change(destination, { target: { value: "Tokyo" } });
    fireEvent.click(screen.getByRole("button", { name: "Save Preferences" }));

    await waitFor(() => {
      expect(updateUserPreferences).toHaveBeenCalledWith(
        "test-token",
        expect.objectContaining({ destination: "Tokyo", travel_style: "business", min_rating: 4 }),
      );
    });
    expect(await screen.findByRole("status")).toHaveTextContent("Preferences saved successfully.");
  });
});
