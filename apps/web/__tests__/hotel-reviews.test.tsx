import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import HotelReviews from "@/components/HotelReviews";
import { fetchHotelReviews } from "@/lib/api";

vi.mock("@/lib/api", () => ({
  fetchHotelReviews: vi.fn(),
}));

describe("hotel reviews", () => {
  beforeEach(() => {
    vi.mocked(fetchHotelReviews).mockClear();
    vi.mocked(fetchHotelReviews).mockResolvedValue([{
      id: "review-1",
      rating: 4,
      text: "Clean room and friendly staff.",
      sentiment_label: "positive",
      sentiment_score: 0.87,
      created_at: "2025-01-02T12:00:00",
      source: "catalog",
      is_synthetic: true,
    }]);
  });

  it("shows stored review ratings, text, sentiment, and date", async () => {
    render(<HotelReviews hotelId="hotel-1" refreshKey={0} />);

    expect(await screen.findByText("Clean room and friendly staff.")).toBeInTheDocument();
    expect(screen.getByLabelText("4 out of 5 stars")).toBeInTheDocument();
    expect(screen.getByText("positive sentiment")).toBeInTheDocument();
    expect(screen.getByText("Jan 2, 2025")).toBeInTheDocument();
    expect(screen.getByText("Sample data")).toBeInTheDocument();
  });

  it("shows five reviews by default and lets the visitor choose a larger amount", async () => {
    vi.mocked(fetchHotelReviews).mockResolvedValue(
      Array.from({ length: 12 }, (_, index) => ({
        id: `review-${index + 1}`,
        rating: 4,
        text: `Review text ${index + 1}`,
        sentiment_label: "positive" as const,
        sentiment_score: 0.87,
        created_at: "2025-01-02T12:00:00",
        source: "catalog" as const,
        is_synthetic: true,
      })),
    );
    render(<HotelReviews hotelId="hotel-1" refreshKey={0} />);

    expect(await screen.findByText("Review text 5")).toBeInTheDocument();
    expect(screen.queryByText("Review text 6")).not.toBeInTheDocument();
    expect(screen.getByText("Showing 5 of 12 reviews")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "10" }));
    expect(screen.getByText("Review text 10")).toBeInTheDocument();
    expect(screen.queryByText("Review text 11")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "All" }));
    expect(screen.getByText("Review text 12")).toBeInTheDocument();
    expect(screen.getByText("Showing 12 of 12 reviews")).toBeInTheDocument();
  });

  it("reloads reviews after a successful submission refresh", async () => {
    const { rerender } = render(<HotelReviews hotelId="hotel-1" refreshKey={0} />);
    await screen.findByText("Clean room and friendly staff.");

    rerender(<HotelReviews hotelId="hotel-1" refreshKey={1} />);
    await waitFor(() => expect(fetchHotelReviews).toHaveBeenCalledTimes(2));
  });

  it("shows a clear empty state when a hotel has no submitted reviews", async () => {
    vi.mocked(fetchHotelReviews).mockResolvedValue([]);
    render(<HotelReviews hotelId="hotel-2" refreshKey={0} />);

    expect(await screen.findByText("No catalog or TripSense reviews are available for this hotel yet.")).toBeInTheDocument();
  });
});
