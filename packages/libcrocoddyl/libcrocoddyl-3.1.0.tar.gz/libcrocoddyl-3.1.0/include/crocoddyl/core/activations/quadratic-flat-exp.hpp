///////////////////////////////////////////////////////////////////////////////
// BSD 3-Clause License
//
// Copyright (C) 2020-2025, LAAS-CNRS, University of Edinburgh,
//                          Heriot-Watt University
// Copyright note valid unless otherwise stated in individual files.
// All rights reserved.
///////////////////////////////////////////////////////////////////////////////

#ifndef CROCODDYL_CORE_ACTIVATIONS_QUADRATIC_FLAT_EXP_HPP_
#define CROCODDYL_CORE_ACTIVATIONS_QUADRATIC_FLAT_EXP_HPP_

#include "crocoddyl/core/activation-base.hpp"
#include "crocoddyl/core/fwd.hpp"

namespace crocoddyl {

/*
 * @brief Quadratic-flat-exp activation
 *
 * This activation function describes a quadratic exponential activation
 * depending on the square norm of a residual vector, i.e. \f[ \begin{equation}
 * 1 - exp(\|\mathbf{r}\|^2 / \alpha) \end{equation} \f] where \f$\alpha\f$
 * defines the width of the quadratic basin, \f$r\f$ is the scalar residual,
 * \f$nr\f$ is the dimension of the residual vector. Far
 * away from zero, the quadFlat activation is nearly flat.
 *
 * The computation of the function and it derivatives are carried out in
 * `calc()` and `caldDiff()`, respectively.
 *
 * \sa `calc()`, `calcDiff()`, `createData()`
 */
template <typename _Scalar>
class ActivationModelQuadFlatExpTpl
    : public ActivationModelAbstractTpl<_Scalar> {
 public:
  EIGEN_MAKE_ALIGNED_OPERATOR_NEW
  CROCODDYL_DERIVED_CAST(ActivationModelBase, ActivationModelQuadFlatExpTpl)

  typedef _Scalar Scalar;
  typedef MathBaseTpl<Scalar> MathBase;
  typedef ActivationModelAbstractTpl<Scalar> Base;
  typedef ActivationDataAbstractTpl<Scalar> ActivationDataAbstract;
  typedef ActivationDataQuadFlatExpTpl<Scalar> Data;
  typedef typename MathBase::VectorXs VectorXs;
  typedef typename MathBase::MatrixXs MatrixXs;

  /*
   * @brief Initialize the quadratic-flat-exp activation model
   *
   * The default `alpha` value is defined as 1.
   *
   * @param[in] nr     Dimension of the residual vector
   * @param[in] alpha  Width of quadratic basin (default: 1.)
   */

  explicit ActivationModelQuadFlatExpTpl(const std::size_t nr,
                                         const Scalar alpha = Scalar(1.))
      : Base(nr), alpha_(alpha) {
    if (alpha < Scalar(0.)) {
      throw_pretty("Invalid argument: " << "alpha should be a positive value");
    }
  };
  virtual ~ActivationModelQuadFlatExpTpl() = default;

  /*
   * @brief Compute the quadratic-flat-exp function
   *
   * @param[in] data  Quadratic-flat activation data
   * @param[in] r     Residual vector \f$\mathbf{r}\in\mathbb{R}^{nr}\f$
   */
  virtual void calc(const std::shared_ptr<ActivationDataAbstract>& data,
                    const Eigen::Ref<const VectorXs>& r) override {
    if (static_cast<std::size_t>(r.size()) != nr_) {
      throw_pretty(
          "Invalid argument: " << "r has wrong dimension (it should be " +
                                      std::to_string(nr_) + ")");
    }
    std::shared_ptr<Data> d = std::static_pointer_cast<Data>(data);

    d->a0 = exp(-r.squaredNorm() / alpha_);
    data->a_value = Scalar(1.0) - d->a0;
  };

  /*
   * @brief Compute the derivatives of the quadratic-flat-exp function
   *
   * @param[in] data  Quadratic-flat activation data
   * @param[in] r     Residual vector \f$\mathbf{r}\in\mathbb{R}^{nr}\f$
   */
  virtual void calcDiff(const std::shared_ptr<ActivationDataAbstract>& data,
                        const Eigen::Ref<const VectorXs>& r) override {
    if (static_cast<std::size_t>(r.size()) != nr_) {
      throw_pretty(
          "Invalid argument: " << "r has wrong dimension (it should be " +
                                      std::to_string(nr_) + ")");
    }
    std::shared_ptr<Data> d = std::static_pointer_cast<Data>(data);

    d->a1 = Scalar(2.0) / alpha_ * d->a0;
    data->Ar = d->a1 * r;
    data->Arr.diagonal() = -Scalar(2.0) * d->a1 * r.array().square() / alpha_;
    data->Arr.diagonal().array() += d->a1;
  };

  /**
   * @brief Create the quadratic-flat-exp activation data
   *
   * @return the activation data
   */
  virtual std::shared_ptr<ActivationDataAbstract> createData() override {
    std::shared_ptr<Data> data =
        std::allocate_shared<Data>(Eigen::aligned_allocator<Data>(), this);
    return data;
  };

  template <typename NewScalar>
  ActivationModelQuadFlatExpTpl<NewScalar> cast() const {
    typedef ActivationModelQuadFlatExpTpl<NewScalar> ReturnType;
    ReturnType res(nr_, scalar_cast<NewScalar>(alpha_));
    return res;
  }

  Scalar get_alpha() const { return alpha_; };
  void set_alpha(const Scalar alpha) { alpha_ = alpha; };

  /**
   * @brief Print relevant information of the quadratic flat-exp model
   *
   * @param[out] os  Output stream object
   */
  virtual void print(std::ostream& os) const override {
    os << "ActivationModelQuadFlatExp {nr=" << nr_ << ", a=" << alpha_ << "}";
  }

 protected:
  using Base::nr_;  //!< Dimension of the residual vector

 private:
  Scalar alpha_;  //!< Width of quadratic basin
};

/*
 * @brief Data structure of the quadratic-flat-exp activation
 *
 * @param[in] a0  computed in calc to avoid recomputation
 * @param[in] a1  computed in calcDiff to avoid recomputation
 */
template <typename _Scalar>
struct ActivationDataQuadFlatExpTpl
    : public ActivationDataAbstractTpl<_Scalar> {
  EIGEN_MAKE_ALIGNED_OPERATOR_NEW

  typedef _Scalar Scalar;
  typedef MathBaseTpl<Scalar> MathBase;
  typedef typename MathBase::VectorXs VectorXs;
  typedef typename MathBase::DiagonalMatrixXs DiagonalMatrixXs;
  typedef ActivationDataAbstractTpl<Scalar> Base;

  template <typename Activation>
  explicit ActivationDataQuadFlatExpTpl(Activation* const activation)
      : Base(activation), a0(Scalar(0)), a1(Scalar(0)) {}
  virtual ~ActivationDataQuadFlatExpTpl() = default;

  Scalar a0;
  Scalar a1;

  using Base::a_value;
  using Base::Ar;
  using Base::Arr;
};

}  // namespace crocoddyl

CROCODDYL_DECLARE_EXTERN_TEMPLATE_CLASS(
    crocoddyl::ActivationModelQuadFlatExpTpl)
CROCODDYL_DECLARE_EXTERN_TEMPLATE_STRUCT(
    crocoddyl::ActivationDataQuadFlatExpTpl)

#endif  // CROCODDYL_CORE_ACTIVATIONS_QUADRATIC_FLAT_EXP_HPP_
