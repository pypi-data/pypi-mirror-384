#ifdef __cplusplus
//....This is needed for C++, otherwise this header works only for C
extern "C" {
#endif

// @brief Read the boundary conditions (optical reflexions) on the external volume(s)
//
// @param[in]    input_data_file_complete_name     : complete name of the input data file
// @param[inout] position_in_input_data_file       : position reached in the input data file
extern void moret_read_boundary_conditions_c(char *input_data_file_complete_name, long &position_in_input_data_file);

// @brief Set the pointers to external procedures required by boundary conditions procedures
//
// @param[in] external_check_face_for_boundary_condition   : pointer to routine to check the face specified for boundary condition, get the face index and return an error if the face is unknown or if it cannot be applied boundary condition
// @param[in] external_get_normal_vector                   : pointer to routine to get the normal vector of the current surface
// @param[in] external_rand_bound_cond                     : pointer to function to get a random number for the boundary conditions
extern void moret_set_boundary_conditions_ptr_to_ext_proc_c(void (*external_check_face_for_boundary_condition) (char*, int&), void (*external_get_normal_vector) (double[3]), double (*external_rand_bound_cond) (void));

// @brief Manage boundary condition (optical reflexion or leakage) on the current external face
//
// @param[in]    external_face_index   : global index of the external face
// @param[inout] cos_dir[3]            : direction cosines before and after reflexion
// @param[out]   leak                  : true if neutron is not reflected
extern void moret_manage_boundary_condition_c(int &external_face_index, double cos_dir[3], bool &leak);

// @brief Get a word describing the boundary condition of the face: the value of the reflexion coefficient (0 for leak, 1 for total reflexion)
//
// @param[in]    face        :  index of the face
// @param[inout] word_length :  length of the word
// @param[inout] word        :  describing word if length sufficient (optional)
extern void moret_get_boundary_condition_word_c(int &face, int &word_length, char *word);

#ifdef __cplusplus
}
#endif
