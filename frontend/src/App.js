import React, { useEffect, useMemo, useState } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useNavigate,
  useParams,
} from "react-router-dom";
import "./App.css";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";
const MEDIA_BASE =
  process.env.REACT_APP_MEDIA_BASE_URL || "http://localhost:8000";

function ListingsPage() {
  const navigate = useNavigate();
  const {
    stateSlug: stateSlugParam,
    districtSlug: districtSlugParam,
    citySlug: citySlugParam,
    categorySlug: categorySlugParam,
  } = useParams();

  // ---------- auth ----------
  const [token, setToken] = useState(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [loginSource, setLoginSource] = useState(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  // ---------- categories ----------
  const [categories, setCategories] = useState([]);
  const [selectedCategoryId, setSelectedCategoryId] = useState(null);
  const [selectedSubCategoryId, setSelectedSubCategoryId] = useState(null);

  // ---------- listings / filters ----------
  const [listings, setListings] = useState([]);
  const [searchText, setSearchText] = useState("");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");

  // ---------- sell modal ----------
  const [sellModalOpen, setSellModalOpen] = useState(false);
  const [newListing, setNewListing] = useState({
    title: "",
    category: null,
    price: "",
  });
  const [newListingImages, setNewListingImages] = useState(null);

  // ---------- location hierarchy ----------
  const [states, setStates] = useState([]);
  const [districts, setDistricts] = useState([]);
  const [cities, setCities] = useState([]);
  const [localities, setLocalities] = useState([]);

  const [selectedStateSlug, setSelectedStateSlug] = useState(
    stateSlugParam || null
  );
  const [selectedDistrictSlug, setSelectedDistrictSlug] = useState(
    districtSlugParam || null
  );
  const [selectedCitySlug, setSelectedCitySlug] = useState(
    citySlugParam || null
  );
  const [selectedLocalitySlug, setSelectedLocalitySlug] = useState(null);

  // ---------- helpers ----------

  const categoriesByParent = useMemo(() => {
    const map = {};
    categories.forEach((cat) => {
      const parentId = cat.parent_id || 0;
      if (!map[parentId]) map[parentId] = [];
      map[parentId].push(cat);
    });
    return map;
  }, [categories]);

  const flatCategories = useMemo(() => categories, [categories]);

  const selectedCategorySlug = useMemo(() => {
    if (categorySlugParam) return categorySlugParam;
    const id = selectedSubCategoryId || selectedCategoryId;
    if (!id) return null;
    const cat = flatCategories.find((c) => c.id === id);
    return cat ? cat.slug : null;
  }, [categorySlugParam, flatCategories, selectedCategoryId, selectedSubCategoryId]);

  // sync selected category when URL has categorySlug
  useEffect(() => {
    if (!categorySlugParam || flatCategories.length === 0) return;
    const cat = flatCategories.find((c) => c.slug === categorySlugParam);
    if (cat) {
      setSelectedCategoryId(cat.parent_id ? cat.parent_id : cat.id);
      if (cat.parent_id) setSelectedSubCategoryId(cat.id);
      else setSelectedSubCategoryId(null);
    }
  }, [categorySlugParam, flatCategories]);

  // ---------- fetches ----------

  const fetchCategories = async () => {
    try {
      const res = await fetch(`${API_URL}/categories`);
      if (!res.ok) {
        console.error("Failed to fetch categories", await res.text());
        return;
      }
      const data = await res.json();
      setCategories(data);
      if (data.length > 0 && !newListing.category) {
        setNewListing((prev) => ({ ...prev, category: data[0].id }));
      }
    } catch (e) {
      console.error("Error fetching categories", e);
    }
  };

  const fetchStates = async () => {
    try {
      const res = await fetch(`${API_URL}/states`);
      if (!res.ok) {
        console.error("Failed to fetch states", await res.text());
        return;
      }
      const data = await res.json();
      setStates(data);
    } catch (e) {
      console.error("Error fetching states", e);
    }
  };

  const fetchDistricts = async (stateSlugVal) => {
    if (!stateSlugVal) return;
    try {
      const res = await fetch(`${API_URL}/states/${stateSlugVal}/districts`);
      if (!res.ok) {
        console.error("Failed to fetch districts", await res.text());
        return;
      }
      const data = await res.json();
      setDistricts(data);
    } catch (e) {
      console.error("Error fetching districts", e);
    }
  };

  const fetchCities = async (stateSlugVal, districtSlugVal) => {
    if (!stateSlugVal || !districtSlugVal) return;
    try {
      const res = await fetch(
        `${API_URL}/states/${stateSlugVal}/districts/${districtSlugVal}/cities`
      );
      if (!res.ok) {
        console.error("Failed to fetch cities", await res.text());
        return;
      }
      const data = await res.json();
      setCities(data);
    } catch (e) {
      console.error("Error fetching cities", e);
    }
  };

  const fetchLocalities = async (stateSlugVal, districtSlugVal, citySlugVal) => {
    if (!stateSlugVal || !districtSlugVal || !citySlugVal) return;
    try {
      const res = await fetch(
        `${API_URL}/states/${stateSlugVal}/districts/${districtSlugVal}/cities/${citySlugVal}/localities`
      );
      if (!res.ok) {
        console.error("Failed to fetch localities", await res.text());
        return;
      }
      const data = await res.json();
      setLocalities(data);
    } catch (e) {
      console.error("Error fetching localities", e);
    }
  };

  const fetchListings = async () => {
    try {
      const params = new URLSearchParams();

      if (searchText) params.append("location", searchText);
      if (minPrice) params.append("min_price", minPrice);
      if (maxPrice) params.append("max_price", maxPrice);

      if (selectedCategorySlug) {
        params.append("category_slug", selectedCategorySlug);
      }
      if (selectedStateSlug) params.append("state_slug", selectedStateSlug);
      if (selectedDistrictSlug)
        params.append("district_slug", selectedDistrictSlug);
      if (selectedCitySlug) params.append("city_slug", selectedCitySlug);
      if (selectedLocalitySlug)
        params.append("locality_slug", selectedLocalitySlug);

      const url = `${API_URL}/listings-with-images${
        params.toString() ? `?${params.toString()}` : ""
      }`;

      const res = await fetch(url);
      if (!res.ok) {
        console.error("Failed to fetch listings", await res.text());
        setListings([]);
        return;
      }
      const data = await res.json();
      setListings(data);
    } catch (e) {
      console.error("Error fetching listings", e);
    }
  };

  // ---------- effects ----------

  useEffect(() => {
    fetchCategories();
    fetchStates();
  }, []);

  // initialize hierarchy from URL slugs
  useEffect(() => {
    if (stateSlugParam) {
      setSelectedStateSlug(stateSlugParam);
      fetchDistricts(stateSlugParam);
    }
    if (stateSlugParam && districtSlugParam) {
      setSelectedDistrictSlug(districtSlugParam);
      fetchCities(stateSlugParam, districtSlugParam);
    }
    if (stateSlugParam && districtSlugParam && citySlugParam) {
      setSelectedCitySlug(citySlugParam);
      fetchLocalities(stateSlugParam, districtSlugParam, citySlugParam);
    }
  }, [stateSlugParam, districtSlugParam, citySlugParam]);

  // normalize hierarchy so higher level clears deeper filters
  useEffect(() => {
    // only state -> clear district, city, locality
    if (selectedStateSlug && !selectedDistrictSlug) {
      setSelectedDistrictSlug(null);
      setSelectedCitySlug(null);
      setSelectedLocalitySlug(null);
    }

    // state + district, but no city -> clear city, locality
    if (selectedStateSlug && selectedDistrictSlug && !selectedCitySlug) {
      setSelectedCitySlug(null);
      setSelectedLocalitySlug(null);
    }

    // state + district + city, but no locality -> clear locality
    if (
      selectedStateSlug &&
      selectedDistrictSlug &&
      selectedCitySlug &&
      !selectedLocalitySlug
    ) {
      setSelectedLocalitySlug(null);
    }
  }, [
    selectedStateSlug,
    selectedDistrictSlug,
    selectedCitySlug,
    selectedLocalitySlug,
  ]);

  useEffect(() => {
    fetchListings();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    searchText,
    minPrice,
    maxPrice,
    selectedCategorySlug,
    selectedStateSlug,
    selectedDistrictSlug,
    selectedCitySlug,
    selectedLocalitySlug,
  ]);

  // ---------- URL builder ----------

  const buildListingsPath = (
    stateSlugVal,
    districtSlugVal,
    citySlugVal,
    categorySlugVal
  ) => {
    const parts = ["/listings"];

    if (stateSlugVal) {
      parts.push(stateSlugVal);
      if (districtSlugVal) {
        parts.push(districtSlugVal);
        if (citySlugVal) {
          parts.push(citySlugVal);
        }
      }
    }

    if (categorySlugVal) {
      parts.push("category", categorySlugVal);
    }

    return parts.join("/").replace(/\/+/g, "/");
  };

  // ---------- handlers: location selection ----------

  const onStateSelect = async (stateSlugVal) => {
    const value = stateSlugVal || null;
    setSelectedStateSlug(value);
    setSelectedDistrictSlug(null);
    setSelectedCitySlug(null);
    setSelectedLocalitySlug(null);
    setDistricts([]);
    setCities([]);
    setLocalities([]);
    navigate(
      buildListingsPath(value, null, null, selectedCategorySlug || categorySlugParam)
    );
    if (value) await fetchDistricts(value);
  };

  const onDistrictSelect = async (districtSlugVal) => {
    const value = districtSlugVal || null;
    setSelectedDistrictSlug(value);
    setSelectedCitySlug(null);
    setSelectedLocalitySlug(null);
    setCities([]);
    setLocalities([]);
    navigate(
      buildListingsPath(
        selectedStateSlug,
        value,
        null,
        selectedCategorySlug || categorySlugParam
      )
    );
    if (selectedStateSlug && value) {
      await fetchCities(selectedStateSlug, value);
    }
  };

  const onCitySelect = async (citySlugVal) => {
    const value = citySlugVal || null;
    setSelectedCitySlug(value);
    setSelectedLocalitySlug(null);
    setLocalities([]);
    navigate(
      buildListingsPath(
        selectedStateSlug,
        selectedDistrictSlug,
        value,
        selectedCategorySlug || categorySlugParam
      )
    );
    if (selectedStateSlug && selectedDistrictSlug && value) {
      await fetchLocalities(selectedStateSlug, selectedDistrictSlug, value);
    }
  };

  const onLocalitySelect = (localitySlugVal) => {
    const value = localitySlugVal || null;
    setSelectedLocalitySlug(value);

    // locality should not change the path segments, only query filtering
    navigate(
      buildListingsPath(
        selectedStateSlug,
        selectedDistrictSlug,
        selectedCitySlug,
        selectedCategorySlug || categorySlugParam
      )
    );
  };

  // ---------- handlers: category selection ----------

  const handleCategoryClick = (cat) => {
    setSelectedCategoryId(cat.id);
    setSelectedSubCategoryId(null);
    navigate(
      buildListingsPath(
        selectedStateSlug,
        selectedDistrictSlug,
        selectedCitySlug,
        cat.slug
      )
    );
  };

  const handleSubCategoryClick = (sub) => {
    setSelectedCategoryId(sub.parent_id || sub.id);
    setSelectedSubCategoryId(sub.id);
    navigate(
      buildListingsPath(
        selectedStateSlug,
        selectedDistrictSlug,
        selectedCitySlug,
        sub.slug
      )
    );
  };

  // ---------- auth handlers ----------

  const openLoginModal = (source = null) => {
    setLoginSource(source);
    setIsRegisterMode(false);
    setAuthModalOpen(true);
  };

  const openRegisterModal = () => {
    setIsRegisterMode(true);
    setAuthModalOpen(true);
  };

  const closeAuthModal = () => {
    setAuthModalOpen(false);
    setEmail("");
    setPassword("");
    setLoginSource(null);
  };

  const handleRegisterOrLogin = async () => {
    const endpoint = isRegisterMode ? "/register" : "/login";
    try {
      const res = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        alert(data?.detail || data?.error || "Auth failed");
        return;
      }
      if (!isRegisterMode) {
        const t = data?.access_token || data?.token;
        if (!t) {
          alert("Token missing in response");
          return;
        }
        setToken(`Bearer ${t}`);
        setIsLoggedIn(true);
        if (loginSource === "sell") {
          setSellModalOpen(true);
        }
      }
      closeAuthModal();
    } catch (e) {
      console.error("Auth error", e);
      alert("Network error");
    }
  };

  const handleLogout = () => {
    setToken(null);
    setIsLoggedIn(false);
  };

  // ---------- sell / listing creation ----------

  const openSellFlow = () => {
    if (!isLoggedIn) {
      openLoginModal("sell");
      return;
    }
    setSellModalOpen(true);
  };

  const closeSellModal = () => {
    setSellModalOpen(false);
    setNewListing({
      title: "",
      category: categories[0]?.id || null,
      price: "",
    });
    setNewListingImages(null);
  };

  const handleNewListingChange = (field, value) => {
    setNewListing((prev) => ({ ...prev, [field]: value }));
  };

const createListing = async () => {
  if (!isLoggedIn || !token) {
    alert("Please log in first.");
    openLoginModal("sell");
    return;
  }

  if (!newListing.title || !newListing.price || !newListing.category) {
    alert("Title, price, and category are required.");
    return;
  }

  if (!selectedStateSlug || !selectedDistrictSlug || !selectedCitySlug || !selectedLocalitySlug) {
    alert("Please select state, district, city and locality as location.");
    return;
  }

  if (!newListingImages || newListingImages.length === 0) {
    alert("Please upload at least one image.");
    return;
  }

  try {
    const body = {
      title: newListing.title,
      category: newListing.category,
      price: parseFloat(newListing.price),
      state_slug: selectedStateSlug,
      district_slug: selectedDistrictSlug,
      city_slug: selectedCitySlug,
      locality_slug: selectedLocalitySlug,
      is_active: true,
    };

    const res = await fetch(`${API_URL}/listing/create`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: token,
      },
      body: JSON.stringify(body),
    });

    const data = await res.json();
    if (!res.ok) {
      alert(data?.detail || data?.error || data?.message || "Create failed");
      return;
    }

    const listingId = data.id;
    if (!listingId) {
      alert("Listing created but ID missing in response.");
      return;
    }

    for (let i = 0; i < newListingImages.length; i++) {
      const file = newListingImages[i];
      const formData = new FormData();
      formData.append("image", file);

      const imgRes = await fetch(
        `${API_URL}/listing/${listingId}/image/upload`,
        {
          method: "POST",
          headers: {
            Authorization: token,
          },
          body: formData,
        }
      );

      if (!imgRes.ok) {
        console.error("Image upload failed", await imgRes.text());
      }
    }

    alert("Listing created with images.");
    closeSellModal();
    fetchListings();
  } catch (e) {
    console.error("Error creating listing", e);
    alert("Network error during listing creation.");
  }
};

  // ---------- render helpers ----------

  const renderCategoryMenu = () => {
    const topLevel = categoriesByParent[0] || [];

    return (
      <nav className="category-bar">
        {topLevel.map((cat) => {
          const children = categoriesByParent[cat.id] || [];
          const isActiveTop =
            (!selectedSubCategoryId && selectedCategoryId === cat.id) ||
            selectedCategorySlug === cat.slug;

          return (
            <div key={cat.id} className="category-top-item">
              <button
                type="button"
                className={`cat-btn ${isActiveTop ? "active" : ""}`}
                onClick={() => handleCategoryClick(cat)}
              >
                {cat.name}
              </button>

              {children.length > 0 && (
                <div className="dropdown">
                  {children.map((sub) => {
                    const isActiveSub =
                      selectedSubCategoryId === sub.id ||
                      selectedCategorySlug === sub.slug;
                    return (
                      <button
                        key={sub.id}
                        type="button"
                        className={isActiveSub ? "dropdown-item active" : "dropdown-item"}
                        onClick={() => handleSubCategoryClick(sub)}
                      >
                        {sub.name}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </nav>
    );
  };

  const renderLocationFilterControls = () => (
    <div className="filter-group">
      <label className="field-inline">
        <span>State</span>
        <select
          value={selectedStateSlug || ""}
          onChange={(e) => onStateSelect(e.target.value || null)}
        >
          <option value="">All states</option>
          {states.map((s) => (
            <option key={s.code} value={s.slug}>
              {s.name}
            </option>
          ))}
        </select>
      </label>

      {selectedStateSlug && (
        <label className="field-inline">
          <span>District</span>
          <select
            value={selectedDistrictSlug || ""}
            onChange={(e) => onDistrictSelect(e.target.value || null)}
          >
            <option value="">All districts</option>
            {districts.map((d) => (
              <option key={d.code} value={d.slug}>
                {d.name}
              </option>
            ))}
          </select>
        </label>
      )}

      {selectedDistrictSlug && (
        <label className="field-inline">
          <span>City</span>
          <select
            value={selectedCitySlug || ""}
            onChange={(e) => onCitySelect(e.target.value || null)}
          >
            <option value="">All cities</option>
            {cities.map((c) => (
              <option key={c.code} value={c.slug}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
      )}

      {selectedCitySlug && (
        <label className="field-inline">
          <span>Locality</span>
          <select
            value={selectedLocalitySlug || ""}
            onChange={(e) => onLocalitySelect(e.target.value || null)}
          >
            <option value="">All localities</option>
            {localities.map((l) => (
              <option key={l.code} value={l.slug}>
                {l.name}
              </option>
            ))}
          </select>
        </label>
      )}
    </div>
  );

  const renderLocationSelectorForForm = () => (
    <div className="location-selector">
      <select
        value={selectedStateSlug || ""}
        onChange={(e) => onStateSelect(e.target.value || null)}
      >
        <option value="">Select state</option>
        {states.map((s) => (
          <option key={s.code} value={s.slug}>
            {s.name}
          </option>
        ))}
      </select>

      {selectedStateSlug && (
        <select
          value={selectedDistrictSlug || ""}
          onChange={(e) => onDistrictSelect(e.target.value || null)}
        >
          <option value="">Select district</option>
          {districts.map((d) => (
            <option key={d.code} value={d.slug}>
              {d.name}
            </option>
          ))}
        </select>
      )}

      {selectedDistrictSlug && (
        <select
          value={selectedCitySlug || ""}
          onChange={(e) => onCitySelect(e.target.value || null)}
        >
          <option value="">Select city</option>
          {cities.map((c) => (
            <option key={c.code} value={c.slug}>
              {c.name}
            </option>
          ))}
        </select>
      )}

      {selectedCitySlug && (
        <select
          value={selectedLocalitySlug || ""}
          onChange={(e) => onLocalitySelect(e.target.value || null)}
        >
          <option value="">Select locality</option>
          {localities.map((l) => (
            <option key={l.code} value={l.slug}>
              {l.name}
            </option>
          ))}
        </select>
      )}
    </div>
  );

  const renderListingsGrid = () => {
    if (!listings || listings.length === 0) {
      return <div className="empty-state">No listings found.</div>;
    }

    return (
      <div className="listing-grid">
        {listings.map((listing) => {
          const primaryImage =
            listing.images && listing.images.length > 0
              ? listing.images[0]
              : null;
          const imgSrc = primaryImage
            ? `${MEDIA_BASE}${primaryImage.image}`
            : "https://via.placeholder.com/300x200?text=No+Image";

          return (
            <div key={listing.id} className="listing-card">
              <img
                src={imgSrc}
                alt={listing.title}
                className="listing-image"
              />
              <div className="listing-info">
                <h3>{listing.title}</h3>
                <p className="price">₹ {listing.price}</p>
                <p className="location">{listing.location}</p>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  // ---------- main render ----------

  return (
    <div className="page-root">
      <header className="navbar">
        <div className="logo">Huduku</div>
        {renderCategoryMenu()}
        <div className="nav-actions">
          {isLoggedIn ? (
            <button className="btn" onClick={handleLogout}>
              Logout
            </button>
          ) : (
            <>
              <button className="btn" onClick={() => openLoginModal(null)}>
                Login
              </button>
              <button className="btn" onClick={openRegisterModal}>
                Register
              </button>
            </>
          )}
          <button className="btn primary" onClick={openSellFlow}>
            Sell
          </button>
        </div>
      </header>

      <main className="layout">
        <section className="filter-bar">
          <div className="filter-group">
            <input
              type="text"
              placeholder="Search by text"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
            />
            <input
              type="number"
              placeholder="Min price"
              value={minPrice}
              onChange={(e) => setMinPrice(e.target.value)}
            />
            <input
              type="number"
              placeholder="Max price"
              value={maxPrice}
              onChange={(e) => setMaxPrice(e.target.value)}
            />
          </div>
          {renderLocationFilterControls()}
        </section>

        <section className="listing-section">{renderListingsGrid()}</section>
      </main>

      {authModalOpen && (
        <div className="modal-backdrop">
          <div className="modal">
            <h2>{isRegisterMode ? "Register" : "Login"}</h2>
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <div className="modal-actions">
              <button className="btn" onClick={closeAuthModal}>
                Cancel
              </button>
              <button className="btn primary" onClick={handleRegisterOrLogin}>
                {isRegisterMode ? "Register" : "Login"}
              </button>
            </div>
            <button
              className="link-btn"
              onClick={() => setIsRegisterMode((v) => !v)}
            >
              {isRegisterMode
                ? "Already have an account? Login"
                : "New user? Register"}
            </button>
          </div>
        </div>
      )}

      {sellModalOpen && (
        <div className="modal-backdrop">
          <div className="modal">
            <h2>Create Listing</h2>
            <input
              type="text"
              placeholder="Title"
              value={newListing.title}
              onChange={(e) =>
                handleNewListingChange("title", e.target.value)
              }
            />
            <input
              type="number"
              placeholder="Price"
              value={newListing.price}
              onChange={(e) =>
                handleNewListingChange("price", e.target.value)
              }
            />
            <select
              value={newListing.category || ""}
              onChange={(e) =>
                handleNewListingChange("category", Number(e.target.value))
              }
            >
              <option value="">Select category</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>

            <div className="form-block">
              <span>Location</span>
              {renderLocationSelectorForForm()}
            </div>

            <input
              type="file"
              multiple
              onChange={(e) => setNewListingImages(e.target.files)}
            />

            <div className="modal-actions">
              <button className="btn" onClick={closeSellModal}>
                Cancel
              </button>
              <button className="btn primary" onClick={createListing}>
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        {/* redirect `/` -> `/listings` */}
        <Route path="/" element={<Navigate to="/listings" replace />} />

        <Route path="/listings" element={<ListingsPage />} />
        <Route path="/listings/category/:categorySlug" element={<ListingsPage />} />
        <Route path="/listings/:stateSlug" element={<ListingsPage />} />
        <Route
          path="/listings/:stateSlug/:districtSlug"
          element={<ListingsPage />}
        />
        <Route
          path="/listings/:stateSlug/:districtSlug/:citySlug"
          element={<ListingsPage />}
        />
        <Route
          path="/listings/:stateSlug/:districtSlug/:citySlug/category/:categorySlug"
          element={<ListingsPage />}
        />
      </Routes>
    </Router>
  );
}

export default App;