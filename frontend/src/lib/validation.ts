/**
 * User Input Validation Utility
 * Validates user input for FabFlow Studio ad video creation
 * Requirements: 1.1, 1.2, 1.3, 1.5
 */

export type AspectRatio = '9:16' | '1:1' | '16:9';

// Enhanced FIBO JSON control types
export type MaterialType = 'fabric' | 'leather' | 'metal' | 'wood' | 'glass' | 'plastic' | 'ceramic';
export type StyleMood = 'luxury' | 'minimal' | 'vibrant' | 'natural' | 'tech';

export interface UserInput {
  brandName: string;
  productName: string;
  productDescription: string;
  productImage?: File | null;
  duration: number;
  aspectRatio: AspectRatio;
  // Enhanced fields for FIBO JSON control
  material?: MaterialType | null;
  primaryColor?: string | null;
  secondaryColor?: string | null;
  styleMood?: StyleMood | null;
}

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

const VALID_ASPECT_RATIOS: AspectRatio[] = ['9:16', '1:1', '16:9'];
const VALID_MATERIALS: MaterialType[] = ['fabric', 'leather', 'metal', 'wood', 'glass', 'plastic', 'ceramic'];
const VALID_STYLE_MOODS: StyleMood[] = ['luxury', 'minimal', 'vibrant', 'natural', 'tech'];
const MIN_DURATION = 5;
const MAX_DURATION = 12;
const VALID_IMAGE_MIME_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
const HEX_COLOR_REGEX = /^#[0-9A-Fa-f]{6}$/;

/**
 * Validates user input for ad video creation
 * @param input - Partial user input to validate
 * @returns ValidationResult with isValid flag and array of error messages
 */
export function validateUserInput(input: Partial<UserInput>): ValidationResult {
  const errors: string[] = [];

  // Validate brand name (required)
  if (!input.brandName || input.brandName.trim() === '') {
    errors.push('Brand name is required');
  }

  // Validate product name (required)
  if (!input.productName || input.productName.trim() === '') {
    errors.push('Product name is required');
  }

  // Validate product description (required)
  if (!input.productDescription || input.productDescription.trim() === '') {
    errors.push('Product description is required');
  }

  // Validate duration (5-12 seconds inclusive)
  if (input.duration === undefined || input.duration === null) {
    errors.push('Duration is required');
  } else if (input.duration < MIN_DURATION || input.duration > MAX_DURATION) {
    errors.push(`Duration must be between ${MIN_DURATION} and ${MAX_DURATION} seconds`);
  }

  // Validate aspect ratio
  if (!input.aspectRatio) {
    errors.push('Aspect ratio is required');
  } else if (!VALID_ASPECT_RATIOS.includes(input.aspectRatio)) {
    errors.push(`Aspect ratio must be one of: ${VALID_ASPECT_RATIOS.join(', ')}`);
  }

  // Validate product image (optional, but must be valid MIME type if provided)
  if (input.productImage) {
    if (!VALID_IMAGE_MIME_TYPES.includes(input.productImage.type)) {
      errors.push('Product image must be a JPEG, PNG, or WebP file');
    }
  }

  // Validate material (optional, but must be valid if provided)
  if (input.material && !VALID_MATERIALS.includes(input.material)) {
    errors.push(`Material must be one of: ${VALID_MATERIALS.join(', ')}`);
  }

  // Validate style mood (optional, but must be valid if provided)
  if (input.styleMood && !VALID_STYLE_MOODS.includes(input.styleMood)) {
    errors.push(`Style mood must be one of: ${VALID_STYLE_MOODS.join(', ')}`);
  }

  // Validate primary color (optional, but must be valid hex if provided)
  if (input.primaryColor && !HEX_COLOR_REGEX.test(input.primaryColor)) {
    errors.push('Primary color must be a valid hex color (e.g., #FF5733)');
  }

  // Validate secondary color (optional, but must be valid hex if provided)
  if (input.secondaryColor && !HEX_COLOR_REGEX.test(input.secondaryColor)) {
    errors.push('Secondary color must be a valid hex color (e.g., #FF5733)');
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

/**
 * Validates image file MIME type
 * @param file - File to validate
 * @returns true if file is a valid image type (jpeg, png, webp)
 */
export function isValidImageType(file: File): boolean {
  return VALID_IMAGE_MIME_TYPES.includes(file.type);
}

/**
 * Default values for user input
 * Per Requirement 1.7: defaults to 8 seconds and 9:16 vertical
 */
export const DEFAULT_USER_INPUT: Omit<UserInput, 'brandName' | 'productName' | 'productDescription'> = {
  duration: 8,
  aspectRatio: '9:16',
  productImage: null,
  material: null,
  primaryColor: null,
  secondaryColor: null,
  styleMood: null,
};

/**
 * Validates hex color format
 * @param color - Color string to validate
 * @returns true if valid hex color format (#RRGGBB)
 */
export function isValidHexColor(color: string): boolean {
  return HEX_COLOR_REGEX.test(color);
}

// Export constants for use in components
export { VALID_MATERIALS, VALID_STYLE_MOODS };
