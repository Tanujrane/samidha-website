document.addEventListener("DOMContentLoaded", () => {
    const CART_KEY = "samidha_cart";
    const LANG_KEY = "samidha_language";
    const scrollTargets = document.querySelectorAll(".scroll-reveal, .hero");
    const cartButtons = document.querySelectorAll("[data-add-to-cart]");
    const productOpenButtons = document.querySelectorAll("[data-product-open]");
    const cartToggles = document.querySelectorAll("[data-cart-toggle]");
    const cartCloseButtons = document.querySelectorAll("[data-cart-close]");
    const modalCloseButtons = document.querySelectorAll("[data-modal-close]");
    const languageToggle = document.querySelector("[data-translate-toggle]");
    const cartCount = document.querySelector("[data-cart-count]");
    const cartItemsContainer = document.querySelector("[data-cart-items]");
    const cartTotal = document.querySelector("[data-cart-total]");
    const cartPageItems = document.querySelector("[data-cart-page-items]");
    const cartPageCount = document.querySelector("[data-cart-page-count]");
    const cartPageTotal = document.querySelector("[data-cart-page-total]");
    const checkoutForm = document.querySelector("[data-checkout-form]");
    const checkoutStatus = document.querySelector("[data-checkout-status]");
    const modalImage = document.querySelector("[data-modal-image]");
    const modalCategory = document.querySelector("[data-modal-category]");
    const modalName = document.querySelector("[data-modal-name]");
    const modalDescription = document.querySelector("[data-modal-description]");
    const modalIngredients = document.querySelector("[data-modal-ingredients]");
    const modalPrice = document.querySelector("[data-modal-price]");
    const modalAddButton = document.querySelector("[data-modal-add]");
    const currentLanguage = {
        value: localStorage.getItem(LANG_KEY) || "en",
    };

    const uiText = {
        en: {
            pricePrefix: "Rs. ",
            quantity: "Qty",
            emptyCart: "Your cart is empty. Add a few homemade favorites to get started.",
        },
        mr: {
            pricePrefix: "रु. ",
            quantity: "प्रमाण",
            emptyCart: "तुमचे कार्ट रिकामे आहे. काही घरगुती आवडीचे पदार्थ जोडा.",
        },
    };

    const formatPrice = (value) => `${uiText[currentLanguage.value].pricePrefix}${value}`;
    const buildBackgroundStyle = (imageUrl) =>
        imageUrl
            ? `linear-gradient(rgba(78, 52, 46, 0.12), rgba(78, 52, 46, 0.18)), url("${imageUrl}")`
            : "";

    const setDocumentTitle = () => {
        const body = document.body;
        const title = currentLanguage.value === "mr" ? body.dataset.pageTitleMr : body.dataset.pageTitleEn;

        if (title) {
            document.title = title;
        }
    };

    const applyStaticTranslations = () => {
        document.documentElement.lang = currentLanguage.value === "mr" ? "mr" : "en";

        document.querySelectorAll("[data-en][data-mr]").forEach((element) => {
            element.textContent = currentLanguage.value === "mr" ? element.dataset.mr : element.dataset.en;
        });

        document.querySelectorAll("[data-aria-en][data-aria-mr]").forEach((element) => {
            const value = currentLanguage.value === "mr" ? element.dataset.ariaMr : element.dataset.ariaEn;
            element.setAttribute("aria-label", value);
        });

        document.querySelectorAll("[data-lang-choice]").forEach((element) => {
            element.classList.toggle("active", element.dataset.langChoice === currentLanguage.value);
        });

        setDocumentTitle();
    };

    const getCart = () => {
        try {
            return JSON.parse(localStorage.getItem(CART_KEY)) || [];
        } catch (error) {
            return [];
        }
    };

    const saveCart = (cart) => {
        localStorage.setItem(CART_KEY, JSON.stringify(cart));
    };

    const setCheckoutStatus = (message, isError = false) => {
        if (!checkoutStatus) {
            return;
        }
        checkoutStatus.textContent = message;
        checkoutStatus.classList.remove("is-hidden", "status-success", "status-error");
        checkoutStatus.classList.add(isError ? "status-error" : "status-success");
    };

    const updateCartCount = (cart) => {
        const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);

        if (cartCount) {
            cartCount.textContent = totalItems;
        }

        if (cartPageCount) {
            cartPageCount.textContent = totalItems;
        }
    };

    const renderCartItemsMarkup = (cart) => {
        if (!cart.length) {
            return `<p class="empty-state">${uiText[currentLanguage.value].emptyCart}</p>`;
        }

        return cart
            .map((item) => {
                const name = currentLanguage.value === "mr" ? item.nameMr : item.name;
                const category = currentLanguage.value === "mr" ? item.categoryMr : item.category;

                return `
                    <div class="cart-item">
                        <div class="cart-item-image ${item.imageClass || ""}"${item.imageUrl ? ` style="background-image: ${buildBackgroundStyle(item.imageUrl)}"` : ""}></div>
                        <div>
                            <h4>${name}</h4>
                            <p>${category}</p>
                            <div class="cart-item-controls">
                                <button class="qty-button" type="button" data-cart-action="decrease" data-product-id="${item.id}">-</button>
                                <span>${uiText[currentLanguage.value].quantity}: ${item.quantity}</span>
                                <button class="qty-button" type="button" data-cart-action="increase" data-product-id="${item.id}">+</button>
                            </div>
                        </div>
                        <strong>${formatPrice(item.price * item.quantity)}</strong>
                    </div>
                `;
            })
            .join("");
    };

    const renderCart = () => {
        const cart = getCart();
        const total = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);

        updateCartCount(cart);

        if (cartItemsContainer) {
            cartItemsContainer.innerHTML = renderCartItemsMarkup(cart);
        }

        if (cartPageItems) {
            cartPageItems.innerHTML = renderCartItemsMarkup(cart);
        }

        if (cartTotal) {
            cartTotal.textContent = formatPrice(total);
        }

        if (cartPageTotal) {
            cartPageTotal.textContent = formatPrice(total);
        }
    };

    const buildCheckoutPayload = () => {
        if (!checkoutForm) {
            return null;
        }
        const formData = new FormData(checkoutForm);
        return {
            customer_name: formData.get("customer_name"),
            phone: formData.get("phone"),
            address: formData.get("address"),
            payment_method: formData.get("payment_method"),
            cart: getCart(),
        };
    };

    const addToCart = (product) => {
        const cart = getCart();
        const existingItem = cart.find((item) => item.id === product.id);

        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            cart.push({ ...product, quantity: 1 });
        }

        saveCart(cart);
        renderCart();
        document.body.classList.add("drawer-open");
    };

    const changeQuantity = (productId, delta) => {
        const cart = getCart();
        const item = cart.find((cartItem) => cartItem.id === productId);

        if (!item) {
            return;
        }

        item.quantity += delta;
        saveCart(cart.filter((cartItem) => cartItem.quantity > 0));
        renderCart();
    };

    const buildProductFromDataset = (dataset) => ({
        id: dataset.productId,
        name: dataset.productName,
        nameMr: dataset.productNameMr,
        description: dataset.productDescription,
        descriptionMr: dataset.productDescriptionMr,
        ingredients: dataset.productIngredients,
        ingredientsMr: dataset.productIngredientsMr,
        price: Number(dataset.productPrice),
        imageClass: dataset.productImage,
        imageUrl: dataset.productImageUrl,
        category: dataset.productCategory,
        categoryMr: dataset.productCategoryMr,
    });

    const openModal = (card) => {
        const product = buildProductFromDataset(card.dataset);
        const isMarathi = currentLanguage.value === "mr";

        if (modalImage) {
            modalImage.className = `modal-image ${product.imageClass || ""}`;
            modalImage.style.backgroundImage = product.imageUrl ? buildBackgroundStyle(product.imageUrl) : "";
        }

        if (modalCategory) {
            modalCategory.textContent = isMarathi ? product.categoryMr : product.category;
        }

        if (modalName) {
            modalName.textContent = isMarathi ? product.nameMr : product.name;
        }

        if (modalDescription) {
            modalDescription.textContent = isMarathi ? product.descriptionMr : product.description;
        }

        if (modalIngredients) {
            modalIngredients.textContent = isMarathi ? product.ingredientsMr : product.ingredients;
        }

        if (modalPrice) {
            modalPrice.textContent = formatPrice(product.price);
        }

        if (modalAddButton) {
            modalAddButton.dataset.product = JSON.stringify(product);
        }

        document.body.classList.add("modal-open");
    };

    const refreshOpenModal = () => {
        if (!document.body.classList.contains("modal-open") || !modalAddButton?.dataset.product) {
            return;
        }

        const product = JSON.parse(modalAddButton.dataset.product);
        const isMarathi = currentLanguage.value === "mr";

        if (modalCategory) {
            modalCategory.textContent = isMarathi ? product.categoryMr : product.category;
        }

        if (modalName) {
            modalName.textContent = isMarathi ? product.nameMr : product.name;
        }

        if (modalDescription) {
            modalDescription.textContent = isMarathi ? product.descriptionMr : product.description;
        }

        if (modalIngredients) {
            modalIngredients.textContent = isMarathi ? product.ingredientsMr : product.ingredients;
        }

        if (modalPrice) {
            modalPrice.textContent = formatPrice(product.price);
        }
    };

    const revealOnScroll = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("visible");
                }
            });
        },
        { threshold: 0.15 }
    );

    scrollTargets.forEach((item) => {
        item.classList.add("scroll-reveal");
        revealOnScroll.observe(item);
    });

    document.querySelectorAll('a[href^="#"]').forEach((link) => {
        link.addEventListener("click", (event) => {
            const targetId = link.getAttribute("href");
            const target = document.querySelector(targetId);

            if (!target) {
                return;
            }

            event.preventDefault();
            target.scrollIntoView({ behavior: "smooth", block: "start" });
        });
    });

    cartButtons.forEach((button) => {
        button.addEventListener("click", () => {
            addToCart({
                id: button.dataset.productId,
                name: button.dataset.productName,
                nameMr: button.dataset.productNameMr,
                price: Number(button.dataset.productPrice),
                imageClass: button.dataset.productImage,
                imageUrl: button.dataset.productImageUrl,
                category: button.dataset.productCategory,
                categoryMr: button.dataset.productCategoryMr,
            });
        });
    });

    productOpenButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const card = button.closest(".product-card");

            if (card) {
                openModal(card);
            }
        });
    });

    if (modalAddButton) {
        modalAddButton.addEventListener("click", () => {
            const product = JSON.parse(modalAddButton.dataset.product || "{}");

            if (!product.id) {
                return;
            }

            addToCart(product);
            document.body.classList.remove("modal-open");
        });
    }

    cartToggles.forEach((button) => {
        button.addEventListener("click", () => {
            document.body.classList.add("drawer-open");
        });
    });

    cartCloseButtons.forEach((button) => {
        button.addEventListener("click", () => {
            document.body.classList.remove("drawer-open");
        });
    });

    modalCloseButtons.forEach((button) => {
        button.addEventListener("click", () => {
            document.body.classList.remove("modal-open");
        });
    });

    document.addEventListener("click", (event) => {
        const actionButton = event.target.closest("[data-cart-action]");

        if (actionButton) {
            const delta = actionButton.dataset.cartAction === "increase" ? 1 : -1;
            changeQuantity(actionButton.dataset.productId, delta);
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            document.body.classList.remove("drawer-open");
            document.body.classList.remove("modal-open");
        }
    });

    if (languageToggle) {
        languageToggle.addEventListener("click", () => {
            document.body.classList.add("lang-transition");
            currentLanguage.value = currentLanguage.value === "en" ? "mr" : "en";
            localStorage.setItem(LANG_KEY, currentLanguage.value);
            applyStaticTranslations();
            renderCart();
            refreshOpenModal();

            setTimeout(() => {
                document.body.classList.remove("lang-transition");
            }, 220);
        });
    }

    applyStaticTranslations();
    renderCart();

    if (checkoutForm) {
        checkoutForm.addEventListener("submit", async (event) => {
            event.preventDefault();

            const payload = buildCheckoutPayload();
            if (!payload) {
                return;
            }

            if (!payload.cart.length) {
                setCheckoutStatus("Your cart is empty.", true);
                return;
            }

            const submitButton = checkoutForm.querySelector("[data-place-order-button]");
            if (submitButton) {
                submitButton.disabled = true;
            }

            try {
                if (payload.payment_method === "COD") {
                    const response = await fetch(checkoutForm.dataset.placeOrderUrl, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload),
                    });
                    const result = await response.json();
                    if (!response.ok || !result.ok) {
                        throw new Error(result.message || "Unable to place the order.");
                    }
                    localStorage.removeItem(CART_KEY);
                    renderCart();
                    checkoutForm.reset();
                    setCheckoutStatus(`Order #${result.order_id} placed successfully with Cash on Delivery.`);
                    return;
                }

                if (typeof window.Razorpay === "undefined") {
                    throw new Error("Razorpay is not available right now.");
                }

                const razorpayResponse = await fetch(checkoutForm.dataset.razorpayOrderUrl, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });
                const razorpayData = await razorpayResponse.json();
                if (!razorpayResponse.ok || !razorpayData.ok) {
                    throw new Error(razorpayData.message || "Unable to start Razorpay checkout.");
                }

                const options = {
                    key: razorpayData.key_id,
                    amount: razorpayData.razorpay_order.amount,
                    currency: razorpayData.razorpay_order.currency,
                    name: "Samidha Masale",
                    description: "Order payment",
                    order_id: razorpayData.razorpay_order.id,
                    prefill: razorpayData.customer,
                    notes: { address: razorpayData.address },
                    theme: { color: "#8B1E1E" },
                    handler: async (paymentResult) => {
                        try {
                            const finalPayload = {
                                ...payload,
                                payment_method: "Razorpay",
                                razorpay_order_id: paymentResult.razorpay_order_id,
                                razorpay_payment_id: paymentResult.razorpay_payment_id,
                                razorpay_signature: paymentResult.razorpay_signature,
                            };
                            const finalResponse = await fetch(checkoutForm.dataset.placeOrderUrl, {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify(finalPayload),
                            });
                            const finalData = await finalResponse.json();
                            if (!finalResponse.ok || !finalData.ok) {
                                throw new Error(finalData.message || "Payment succeeded but order saving failed.");
                            }
                            localStorage.removeItem(CART_KEY);
                            renderCart();
                            checkoutForm.reset();
                            setCheckoutStatus(`Order #${finalData.order_id} placed successfully with Razorpay.`);
                        } catch (saveError) {
                            setCheckoutStatus(saveError.message || "Payment succeeded but order saving failed.", true);
                        }
                    },
                };

                const razorpayCheckout = new window.Razorpay(options);
                razorpayCheckout.on("payment.failed", (failure) => {
                    setCheckoutStatus(failure.error.description || "Payment failed.", true);
                });
                razorpayCheckout.open();
            } catch (error) {
                setCheckoutStatus(error.message || "Checkout failed.", true);
            } finally {
                if (submitButton) {
                    submitButton.disabled = false;
                }
            }
        });
    }
});
