/**
 * User Input Validation Utility
 * Validates user input for FabFlow Studio ad video creation
 * Requirements: 1.1, 1.3, 1.5
 */

export type AspectRatio = '9:16' | '1:1' | '16:9';

export interface UserInput {
  brandName: string;
  productName: string;
  productDescription: string;
  productImage?: File | null;
  duration: number;
  aspectRatio: AspectRatio;
}

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

const VALID_ASPECT_RATIOS: AspectRatio[] = ['9:16', '1:1', '16:9'];
const MIN_DURATION = 5;
const MAX_DURATION = 12;
const VALID_IMAGE_MIME_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

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
};
