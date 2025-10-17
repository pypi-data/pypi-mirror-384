///////////////////////////////////////////////////////////////////////////////
// BSD 3-Clause License
//
// Copyright (C) 2020-2025, LAAS-CNRS, University of Edinburgh,
//                          Heriot-Watt University
// Copyright note valid unless otherwise stated in individual files.
// All rights reserved.
///////////////////////////////////////////////////////////////////////////////

#ifndef CROCODDYL_MULTIBODY_RESIDUALS_CONTROL_GRAVITY_HPP_
#define CROCODDYL_MULTIBODY_RESIDUALS_CONTROL_GRAVITY_HPP_

#include "crocoddyl/core/residual-base.hpp"
#include "crocoddyl/multibody/data/multibody.hpp"
#include "crocoddyl/multibody/states/multibody.hpp"

namespace crocoddyl {

/**
 * @brief Control gravity residual
 *
 * This residual function is defined as
 * \f$\mathbf{r}=\mathbf{u}-\mathbf{g}(\mathbf{q})\f$, where
 * \f$\mathbf{u}\in~\mathbb{R}^{nu}\f$ is the current control input,
 * \f$\mathbf{g}(\mathbf{q})\f$ is the gravity torque corresponding to the
 * current configuration, \f$\mathbf{q}\in~\mathbb{R}^{nq}\f$ the current
 * position joints input. Note that the dimension of the residual vector is
 * obtained from `StateAbstractTpl::get_nv()`.
 *
 * As described in `ResidualModelAbstractTpl()`, the residual value and its
 * Jacobians are calculated by `calc()` and `calcDiff()`, respectively.
 *
 * \sa `ResidualModelAbstractTpl`, `calc()`, `calcDiff()`, `createData()`
 */
template <typename _Scalar>
class ResidualModelControlGravTpl : public ResidualModelAbstractTpl<_Scalar> {
 public:
  EIGEN_MAKE_ALIGNED_OPERATOR_NEW
  CROCODDYL_DERIVED_CAST(ResidualModelBase, ResidualModelControlGravTpl)

  typedef _Scalar Scalar;
  typedef MathBaseTpl<Scalar> MathBase;
  typedef ResidualModelAbstractTpl<Scalar> Base;
  typedef ResidualDataControlGravTpl<Scalar> Data;
  typedef ResidualDataAbstractTpl<Scalar> ResidualDataAbstract;
  typedef StateMultibodyTpl<Scalar> StateMultibody;
  typedef DataCollectorAbstractTpl<Scalar> DataCollectorAbstract;
  typedef typename MathBase::VectorXs VectorXs;
  typedef typename MathBase::MatrixXs MatrixXs;

  /**
   * @brief Initialize the control gravity residual model
   *
   * @param[in] state       State of the multibody system
   * @param[in] nu          Dimension of control vector
   */
  ResidualModelControlGravTpl(std::shared_ptr<StateMultibody> state,
                              const std::size_t nu);

  /**
   * @brief Initialize the control gravity residual model
   *
   * The default `nu` value is obtained from `StateAbstractTpl::get_nv()`.
   *
   * @param[in] state       State of the multibody system
   */
  ResidualModelControlGravTpl(std::shared_ptr<StateMultibody> state);
  virtual ~ResidualModelControlGravTpl() = default;

  /**
   * @brief Compute the control gravity residual
   *
   * @param[in] data  Control residual data
   * @param[in] x     State point \f$\mathbf{x}\in\mathbb{R}^{ndx}\f$
   * @param[in] u     Control input \f$\mathbf{u}\in\mathbb{R}^{nu}\f$
   */
  virtual void calc(const std::shared_ptr<ResidualDataAbstract>& data,
                    const Eigen::Ref<const VectorXs>& x,
                    const Eigen::Ref<const VectorXs>& u) override;

  /**
   * @brief @copydoc Base::calc(const std::shared_ptr<ResidualDataAbstract>&
   * data, const Eigen::Ref<const VectorXs>& x)
   */
  virtual void calc(const std::shared_ptr<ResidualDataAbstract>& data,
                    const Eigen::Ref<const VectorXs>& x) override;

  /**
   * @brief Compute the Jacobians of the control gravity residual
   *
   * @param[in] data  Control residual data
   * @param[in] x     State point \f$\mathbf{x}\in\mathbb{R}^{ndx}\f$
   * @param[in] u     Control input \f$\mathbf{u}\in\mathbb{R}^{nu}\f$
   */
  virtual void calcDiff(const std::shared_ptr<ResidualDataAbstract>& data,
                        const Eigen::Ref<const VectorXs>& x,
                        const Eigen::Ref<const VectorXs>& u) override;

  /**
   * @brief @copydoc Base::calcDiff(const
   * std::shared_ptr<ResidualDataAbstract>& data, const Eigen::Ref<const
   * VectorXs>& x)
   */
  virtual void calcDiff(const std::shared_ptr<ResidualDataAbstract>& data,
                        const Eigen::Ref<const VectorXs>& x) override;

  virtual std::shared_ptr<ResidualDataAbstract> createData(
      DataCollectorAbstract* const data) override;

  /**
   * @brief Cast the control-gravity residual model to a different scalar type.
   *
   * It is useful for operations requiring different precision or scalar types.
   *
   * @tparam NewScalar The new scalar type to cast to.
   * @return ResidualModelControlGravTpl<NewScalar> A residual model with the
   * new scalar type.
   */
  template <typename NewScalar>
  ResidualModelControlGravTpl<NewScalar> cast() const;

  /**
   * @brief Print relevant information of the control-grav residual
   *
   * @param[out] os  Output stream object
   */
  virtual void print(std::ostream& os) const override;

 protected:
  using Base::nu_;
  using Base::state_;
  using Base::v_dependent_;

 private:
  typename StateMultibody::PinocchioModel
      pin_model_;  //!< Pinocchio model used for internal computations
};

template <typename _Scalar>
struct ResidualDataControlGravTpl : public ResidualDataAbstractTpl<_Scalar> {
  EIGEN_MAKE_ALIGNED_OPERATOR_NEW

  typedef _Scalar Scalar;
  typedef MathBaseTpl<Scalar> MathBase;
  typedef ResidualDataAbstractTpl<Scalar> Base;
  typedef StateMultibodyTpl<Scalar> StateMultibody;
  typedef DataCollectorAbstractTpl<Scalar> DataCollectorAbstract;
  typedef pinocchio::DataTpl<Scalar> PinocchioData;

  template <template <typename Scalar> class Model>
  ResidualDataControlGravTpl(Model<Scalar>* const model,
                             DataCollectorAbstract* const data)
      : Base(model, data) {
    // Check that proper shared data has been passed
    DataCollectorActMultibodyTpl<Scalar>* d =
        dynamic_cast<DataCollectorActMultibodyTpl<Scalar>*>(shared);
    if (d == NULL) {
      throw_pretty(
          "Invalid argument: the shared data should be derived from "
          "DataCollectorActMultibodyTpl");
    }
    // Avoids data casting at runtime
    StateMultibody* sm = static_cast<StateMultibody*>(model->get_state().get());
    pinocchio = PinocchioData(*(sm->get_pinocchio().get()));
    actuation = d->actuation;
  }
  virtual ~ResidualDataControlGravTpl() = default;

  PinocchioData pinocchio;  //!< Pinocchio data
  std::shared_ptr<ActuationDataAbstractTpl<Scalar> >
      actuation;  //!< Actuation data
  using Base::r;
  using Base::Ru;
  using Base::Rx;
  using Base::shared;
};

}  // namespace crocoddyl

/* --- Details -------------------------------------------------------------- */
/* --- Details -------------------------------------------------------------- */
/* --- Details -------------------------------------------------------------- */
#include "crocoddyl/multibody/residuals/control-gravity.hxx"

CROCODDYL_DECLARE_EXTERN_TEMPLATE_CLASS(crocoddyl::ResidualModelControlGravTpl)
CROCODDYL_DECLARE_EXTERN_TEMPLATE_STRUCT(crocoddyl::ResidualDataControlGravTpl)

#endif  // CROCODDYL_MULTIBODY_RESIDUALS_CONTROL_GRAVITY_HPP_
